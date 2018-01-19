
import git
import sys
import os
import shutil
import subprocess
import signal

active_procs = []


def close_procs(s, f):
    for pid in active_procs:
        print("Killing " + str(pid))
        # using SIGTERM as a docker workaround for now
        # Needs refactoing and docker stop
        os.kill(pid, signal.SIGTERM)
    sys.exit(0)


signal.signal(signal.SIGINT, close_procs)


def import_config():
    sys.path.append(os.getcwd())
    from config import configure_mbt
    return configure_mbt()


def repo_object(conf):
    repo_dir = os.path.join(os.getcwd(), "master")
    return git.Repo.init(repo_dir)


def add_worktree(repo, loc, branch, ref):
    print("Adding worktree: "+loc)
    if branch in repo.heads:
        # TODO: sanity check the ref
        # TODO: prune
        repo.git.worktree("add", "../"+loc, branch)
    else:
        repo.git.worktree("add", "../"+loc, "-b", branch, ref)
    if os.path.isfile(os.path.join(loc, ".gitmodules")):
        print("... Initializing submodules")
        subrepo = git.Repo(loc)
        for sm in subrepo.submodules:
            sm.update("--init", "--recursive")


def init_mbt(conf, repo):
    with repo.config_writer() as cw:
        if conf.user_name:
            if not cw.has_section("user"):
                cw.add_section("user")
            cw.set("user", "name", conf.user_name)
        if conf.user_email:
            if not cw.has_section("user"):
                cw.add_section("user")
            cw.set("user", "email", conf.user_email)
        pass
    print("Adding remotes...")
    for name, url in conf.remotes.items():
        print("Adding/updating remote '" + name + "': " + url)
        try:
            repo.create_remote(name, url)
        except Exception:
            pass
        repo.remotes[name].fetch()
    print("Checking out versions...")
    for ver in conf.versions:
        print(ver+"...")
        if not os.path.isdir("versions/"+ver):
            add_worktree(repo, "versions/"+ver, ver, "origin/"+ver)


def create_topic(repo, name, versions):
    for ver in versions:
        branch = "ps-"+ver+"-"+name
        add_worktree(repo, "topics/"+name+"/"+ver, branch, ver)


def run_command(args, replace_curr):
    print(args)
    if replace_curr:
        os.execvp(args[0], args)
    else:
        cmd = subprocess.Popen(args,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
        pid = cmd.pid
        active_procs.append(pid)
        while cmd.poll() is None:
            sys.stdout.write(cmd.stdout.readline())
        sys.stdout.write(cmd.stdout.read())
        active_procs.remove(pid)


def exec_docker_command(container, cmd, replace_curr=True, docker_args=[]):
    if replace_curr:
        docker_args += ["-t"]

    docker_args = (["/usr/bin/docker", "exec", "--privileged", "-i"]
                   + docker_args
                   + [container]
                   + cmd
                   )

    run_command(docker_args, replace_curr)


def run_docker_command(img, volumes, work_dir, env, args, replace_curr=True,
                       docker_args=[]):

    def proc_volume_arg(v):
        curr_dir = os.getcwd()
        a = v.split(":", 1)
        if len(a) == 1:
            a.append(a[0])
        if a[0][0] != '/':
            a[0] = curr_dir + "/" + a[0]
            a[1] = "/work/" + a[1]
        return "-v" + a[0] + "/:" + a[1]

    volumes = list(map(proc_volume_arg, volumes))

    def proc_env_arg(v):
        return ["-e", v[0]+"="+v[1]]

    base_env = {"DISPLAY": os.environ["DISPLAY"]}
    env = sum(list(map(proc_env_arg, {**env, **base_env}.items())), [])

    if replace_curr:
        docker_args += ["-t"]

    docker_args = (["/usr/bin/docker", "run", "--privileged", "--rm", "-i"]
                   + volumes
                   + env
                   + ["-w", work_dir]
                   + docker_args
                   + ["--network", "mbt"]
                   + [img]
                   + args
                   )

    run_command(docker_args, replace_curr)


def run_docker_build_command(conf, topic, version, preset, work_dir, args):
    src_dir = os.path.join("topics", topic, version)
    build_dir = os.path.join("topics", topic, version+"-"+preset)

    if not os.path.isdir(build_dir):
        os.mkdir(build_dir)

    buildconf = conf.build_configs[preset]

    volumes = [src_dir+":src",
               build_dir+":build",
               # Required for debugging on the host X
               "/tmp/.X11-unix:/tmp/.X11-unix:ro",
               # Required for git subtree to work correctly,
               # as it uses absolute paths, and needs the master dir
               os.path.join(os.getcwd(), "master")]

    run_docker_command(
            buildconf["image"],
            volumes,
            work_dir,
            buildconf["environment"],
            args
            )


def run_installed_command(conf, topic, version, preset, install_tag, cmd,
                          docker_args=[]):
    src_dir = os.path.join("topics", topic, version)
    install_dir = os.path.join("topics", topic,
                               version+"-"+preset+"-inst"+"-"+install_tag)

    buildconf = conf.build_configs[preset]

    volumes = [src_dir+":src",
               install_dir+":install",
               # Required for debugging on the host X
               "/tmp/.X11-unix:/tmp/.X11-unix:ro",
               # Required for git subtree to work correctly,
               # as it uses absolute paths, and needs the master dir
               os.path.join(os.getcwd(), "master")]

    run_docker_command(
            buildconf["image"],
            volumes,
            "/work/install",
            buildconf["environment"],
            cmd,
            False,
            docker_args
            )


def exec_installed_command(conf, topic, version, preset, install_tag, cmd,
                           replace_current=True, docker_args=[]):
    install_name = "mysqld-" + topic + "-" + version+"-"+preset+"-"+install_tag

    exec_docker_command(
            install_name,
            cmd,
            replace_current,
            docker_args,
            )


def install_build(conf, topic, version, preset, tag, args):
    src_dir = os.path.join("topics", topic, version)
    build_dir = os.path.join("topics", topic, version+"-"+preset)
    install_dir = os.path.join("topics", topic,
                               version+"-"+preset+"-inst"+"-"+tag)

    if not os.path.isdir(install_dir):
        os.mkdir(install_dir)
        os.mkdir(os.path.join(install_dir, "etc"))
        os.mkdir(os.path.join(install_dir, "var"))
        os.mkdir(os.path.join(install_dir, "tmp"))

    config_file = os.path.join(install_dir, "etc", "my.cnf")
    if not os.path.isfile(config_file):

        my_cnf_content = """
[client]
port=10000
socket=/work/install/var/mysql.sock
user=root
[mysqld]
basedir=/work/install/
datadir=/work/install/data
tmpdir=/work/install/tmp
port=10000
socket=/work/install/var/mysql.sock
pid-file=/work/install/var/mysql.pid
console
server-id=1
max_connections=1000
        """

        config = open(os.path.join(install_dir, "etc", "my.cnf"), "w")
        config.write(my_cnf_content)
        config.close()

    buildconf = conf.build_configs[preset]

    volumes = [src_dir+":src",
               build_dir+":build",
               install_dir+":install",
               # Required for git subtree to work correctly,
               # as it uses absolute paths, and needs the master dir
               os.path.join(os.getcwd(), "master")]

    run_docker_command(
            buildconf["image"],
            volumes,
            "/work/build",
            buildconf["environment"],
            ["make", "install"],
            False
            )

    if "--init" in args:

        if version == "5.7":
            init_cmd = ["./bin/mysqld-debug",
                        "--defaults-file=/work/install/etc/my.cnf",
                        "--initialize-insecure",
                        ]
        else:
            init_cmd = ["./scripts/mysql_install_db",
                        "--defaults-file=/work/install/etc/my.cnf",
                        ]

        run_installed_command(
                conf,
                topic,
                version,
                preset,
                tag,
                init_cmd
                )


def run_mysqld(conf, topic, version, preset, tag, args):
    run_installed_command(
            conf,
            topic,
            version,
            preset,
            tag,
            ["./bin/mysqld-debug",
             "--defaults-file=/work/install/etc/my.cnf",
             ] + args,
            ["--expose=10000",
             "-p=10000:10000",
             "--name", "mysqld-"+topic+"-"+version+"-"+preset+"-"+tag,
             "--cpus=1"]
            )


def run_local_mysql(conf, topic, version, preset, tag, args):
    exec_installed_command(
            conf,
            topic,
            version,
            preset,
            tag,
            ["./bin/mysql",
             "--defaults-file=/work/install/etc/my.cnf",
             ] + args
            )


def run_local_bash(conf, topic, version, preset, tag, args):
    exec_installed_command(
            conf,
            topic,
            version,
            preset,
            tag,
            ["/bin/bash",
             ] + args
            )


def create_build(conf, topic, version, preset):
    buildconf = conf.build_configs[preset]

    def proc_cmake_arg(v):
        return "-D"+v[0] + "=" + v[1]

    cmake_args = list(map(proc_cmake_arg, buildconf["config"].items()))

    run_docker_build_command(conf, topic, version, preset, "/work/build",
                             ["cmake", "../src"] + cmake_args)


def build_with_make(conf, topic, version, preset, add_argv):
    run_docker_build_command(conf, topic, version, preset, "/work/build",
                             ["make"] + add_argv)


def delete_build(conf, topic, version, preset):
    build_dir = os.path.join("topics", topic, version+"-"+preset)
    shutil.rmtree(build_dir)


def test_with_mtr(conf, topic, version, preset, add_argv):
    run_docker_build_command(conf, topic, version, preset,
                             "/work/build/mysql-test",
                             ["./mtr"] + add_argv)


def cleanup_repo(conf, force=False):
    # For some reason branch deletion doesn't work from the empty master
    repo = git.Repo("versions/"+conf.versions[0])
    repo.git.worktree("prune")
    for br in repo.heads:
        try:
            deleter = "-D" if force else "-d"
            repo.git.branch(deleter, br.name)
            print("Removed branch: " + br.name)
        except git.exc.GitCommandError as e:
            if "checked out at" not in e.stderr:
                print(e)
            pass


conf = import_config()
repo = repo_object(conf)

if sys.argv[1] == "init":
    init_mbt(conf, repo)

if sys.argv[1] == "create-topic":
    create_topic(repo, sys.argv[2], conf.versions)

if sys.argv[1] == "create-build":
    create_build(conf, sys.argv[2], sys.argv[3], sys.argv[4])

if sys.argv[1] == "delete-build":
    delete_build(conf, sys.argv[2], sys.argv[3], sys.argv[4])

if sys.argv[1] == "make":
    build_with_make(conf, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])

if sys.argv[1] == "install":
    install_build(conf, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
                  sys.argv[6:])

if sys.argv[1] == "run-mysqld":
    run_mysqld(conf, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
               sys.argv[6:])

if sys.argv[1] == "run-mysql-cmd":
    run_local_mysql(conf, sys.argv[2], sys.argv[3], sys.argv[4],
                    sys.argv[5], sys.argv[6:])

if sys.argv[1] == "run-bash":
    run_local_bash(conf, sys.argv[2], sys.argv[3], sys.argv[4],
                   sys.argv[5], sys.argv[6:])

if sys.argv[1] == "mtr":
    test_with_mtr(conf, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])

if sys.argv[1] == "cleanup":
    cleanup_repo(conf, len(sys.argv) >= 3 and sys.argv[2] == "--force")
