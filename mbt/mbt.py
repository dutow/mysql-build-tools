
import git
import sys
import os
import shutil
import subprocess
import signal
import tempfile

from .mbt_root import MbtRoot
from .mbt_params import MbtParams
from .directory_context import DirectoryContext

active_procs = []


def close_procs(s, f):
    for pid in active_procs:
        print("Killing " + str(pid))
        # using SIGTERM as a docker workaround for now
        # Needs refactoing and docker stop
        os.kill(pid, signal.SIGTERM)
    sys.exit(0)


signal.signal(signal.SIGINT, close_procs)


def import_config(root):
    sys.path.append(root.root_dir())
    from mbt_config import configure_mbt
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
    print("Checking out series...")
    for ver in conf.series:
        print(ver+"...")
        if not os.path.isdir("versions/"+ver):
            add_worktree(repo, "versions/"+ver, ver, "origin/"+ver)


def create_topic(repo, param_handler, args):
    param_handler.add_topic_arg()
    ctx = param_handler.parse(args)

    for ver in param_handler.config.series:
        branch = "ps-"+ver+"-"+ctx.topic
        add_worktree(repo, "topics/"+ctx.topic+"/"+ver, branch, ver)


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

    docker_args = (["/usr/bin/docker", "exec", "--privileged", "-i"] +
                   docker_args +
                   [container] +
                   cmd
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

    docker_args = (["/usr/bin/docker", "run", "--privileged", "--rm", "-i", ] +
                   volumes +
                   env +
                   ["-w", work_dir] +
                   docker_args +
                   ["--network", "mbt"] +
                   [img] +
                   args
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
                          docker_args=[], replace_current=False):
    src_dir = os.path.join("topics", topic, version)
    build_dir = os.path.join("topics", topic, version+"-"+preset)

    install_dir = os.path.join("topics", topic,
                               version+"-"+preset+"-inst"+"-"+install_tag)

    buildconf = conf.build_configs[preset]

    volumes = [src_dir+":src",
               install_dir+":install",
               build_dir+":build",
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
            True,
            docker_args
            )


def exec_installed_command(conf, topic, version, preset, install_tag, cmd,
                           replace_current=True, docker_args=[]):
    install_name = "mysqld-" + topic + "-" + version+"-"+preset+"-"+install_tag

    exec_docker_command(
            install_name,
            cmd,
            replace_current,
            docker_args
            )


def run_pull(repo, param_handler, args):
    param_handler.add_remote_arg()
    ctx = param_handler.parse(args)

    print("Pulling from " + ctx.remote)
    repo.remotes[ctx.remote].fetch()
    for ver in param_handler.config.series:
        print(" "+ver+"...")
        repo = git.Repo("versions/"+ver)
        repo.git.pull(ctx.remote, ver)


def run_push(config):
    print("Pushing...")
    for ver in config.series:
        print(" "+ver+"...")
        repo = git.Repo("versions/"+ver)
        repo.git.push()


def detect_build_tool(topic, version, preset):
    build_dir = os.path.join("topics", topic, version+"-"+preset)

    if os.path.isfile(os.path.join(build_dir, "Makefile")):
        return "make"

    if os.path.isfile(os.path.join(build_dir, "build.ninja")):
        return "ninja"

    raise Exception("Couldn't detect build tool")


def detect_mysqld_executable(topic, version, preset):
    # This tries to use the build directory,
    # which has the mysqld executable within sql/
    if version == "8.0":
        ex_dir = os.path.join("topics",
                              topic, version+"-"+preset,
                              "bin")
    else:
        ex_dir = os.path.join("topics",
                              topic,
                              version+"-"+preset,
                              "sql")
    debug_executable = "mysqld-debug"
    release_executable = "mysqld"

    if os.path.isfile(os.path.join(ex_dir, debug_executable)):
        return os.path.join("./bin", debug_executable)

    if os.path.isfile(os.path.join(ex_dir, release_executable)):
        return os.path.join("./bin", release_executable)

    raise Exception("Couldn't find mysqld executable")


def install_build(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_installation_arg()
    param_handler.add_boolean_arg("init")
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    src_dir = os.path.join("topics", ctx.topic, ctx.series)
    build_dir = os.path.join("topics", ctx.topic, ctx.series+"-"+ctx.variant)
    install_dir = os.path.join("topics", ctx.topic,
                               ctx.series+"-"+ctx.variant+"-inst"+"-" +
                               ctx.installation)

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

    buildconf = param_handler.config.build_configs[ctx.variant]

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
            [detect_build_tool(ctx.topic, ctx.series, ctx.variant), "install"],
            False
            )

    if ctx.init:

        if ctx.series == "5.7" or ctx.series == "8.0":
            mysql_exe = detect_mysqld_executable(ctx.topic,
                                                 ctx.series,
                                                 ctx.variant)
            init_cmd = [mysql_exe,
                        "--defaults-file=/work/install/etc/my.cnf",
                        "--initialize-insecure",
                        ]
        else:
            init_cmd = ["./scripts/mysql_install_db",
                        "--defaults-file=/work/install/etc/my.cnf",
                        ]

        run_installed_command(
                param_handler.config,
                ctx.topic,
                ctx.series,
                ctx.variant,
                ctx.installation,
                init_cmd + ctx.remaining_args
                )


def run_mysqld(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_installation_arg()
    param_handler.add_boolean_arg("valgrind")
    param_handler.add_boolean_arg("massif")
    param_handler.add_int_arg("port", 10000)
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    container_name = ("mysqld-"+ctx.topic +
                      "-"+ctx.series +
                      "-"+ctx.variant +
                      "-"+ctx.installation
                      )

    mysqld_cmd = [detect_mysqld_executable(ctx.topic, ctx.series, ctx.variant)]
    if ctx.valgrind:
        mysqld_cmd = ["valgrind"] + mysqld_cmd
    if ctx.massif:
        mysqld_cmd = (["valgrind",
                       "--tool=massif",
                       "--massif-out-file=/work/install/massif.out"]
                      + mysqld_cmd)

    port = str(ctx.port)

    run_installed_command(
            param_handler.config,
            ctx.topic,
            ctx.series,
            ctx.variant,
            ctx.installation,
            mysqld_cmd +
            ["--defaults-file=/work/install/etc/my.cnf"]
            + ctx.remaining_args,
            ["--expose="+port,
             "-p="+port+":"+port,
             "--name", container_name,
             "--cpus=1"]
            )


def exec_local_mysql(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_installation_arg()
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    exec_installed_command(
            param_handler.config,
            ctx.topic,
            ctx.series,
            ctx.variant,
            ctx.installation,
            ["./bin/mysql",
             "--defaults-file=/work/install/etc/my.cnf",
             ] + ctx.remaining_args
            )


def exec_local_bash(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_installation_arg()
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    exec_installed_command(
            param_handler.config,
            ctx.topic,
            ctx.series,
            ctx.variant,
            ctx.installation,
            ["/bin/bash",
             ] + ctx.remaining_args
            )


def run_local_bash(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_installation_arg()
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    run_installed_command(
            param_handler.config,
            ctx.topic,
            ctx.series,
            ctx.variant,
            ctx.installation,
            ["/bin/bash",
             ] + ctx.remaining_args,
            ["-it"],
            True
            )


def create_build(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    buildconf = param_handler.config.build_configs[ctx.variant]

    def proc_cmake_arg(v):
        return "-D"+v[0] + "=" + v[1]

    cmake_args = list(map(proc_cmake_arg, buildconf["config"].items()))

    run_docker_build_command(param_handler.config,
                             ctx.topic,
                             ctx.series,
                             ctx.variant,
                             "/work/build",
                             ["cmake", "../src"]
                             + cmake_args
                             + ctx.remaining_args)


def build_with(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    build_tool = detect_build_tool(ctx.topic, ctx.series, ctx.variant)

    run_docker_build_command(param_handler.config,
                             ctx.topic,
                             ctx.series,
                             ctx.variant,
                             "/work/build",
                             [build_tool]
                             + ctx.remaining_args)


def delete_build(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    ctx = param_handler.parse(args)

    build_dir = os.path.join("topics", ctx.topic, ctx.series+"-"+ctx.variant)
    shutil.rmtree(build_dir)


def test_with_mtr(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    run_docker_build_command(param_handler.config,
                             ctx.topic,
                             ctx.series,
                             ctx.variant,
                             "/work/build/mysql-test",
                             ["eatmydata",  "./mtr"] + ctx.remaining_args)


def asan_symbolize(param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_series_arg()
    param_handler.add_variant_arg()
    param_handler.add_remaining_args()
    ctx = param_handler.parse(args)

    run_docker_build_command(param_handler.config,
                             ctx.topic,
                             ctx.series,
                             ctx.variant,
                             "/work/bin/",
                             ["./asan_symbolize.py"] + ctx.remaining_args)


def cleanup_repo(conf, force=False):
    # For some reason branch deletion doesn't work from the empty master
    repo = git.Repo("versions/"+conf.series[0])
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


def reupmerge(param_handler, args):
    param_handler.add_topic_arg()
    ctx = param_handler.parse(args)

    min_version = '5.6'
    later_versions = ['5.7', '8.0']

    base_branch = "ps-"+min_version+"-"+ctx.topic

    for ver in later_versions:
        next_branch = "ps-"+ver+"-"+ctx.topic
        print("Reupmerging " + base_branch + " to " + next_branch)
        repo = git.Repo("topics/"+ctx.topic+"/"+ver)
        commit_msg = repo.git.log("--format=%B", "-1")
        diff = repo.git.log("-1",
                            "-p",
                            "-m",
                            "--first-parent",
                            "--pretty=email",
                            "--full-index",
                            "--binary")
        name_diff = ''
        name_msg = ''
        with tempfile.NamedTemporaryFile(mode='w') as tmp_diff:
            with tempfile.NamedTemporaryFile(mode='w') as tmp_msg:
                tmp_diff.write(diff)
                tmp_diff.write("\n")
                tmp_diff.flush()
                name_diff = tmp_diff.name
                tmp_msg.write(commit_msg)
                tmp_msg.flush()
                name_msg = tmp_msg.name

                repo.git.reset("--keep", "HEAD~")
                repo.git.merge("-s", "ours", "--no-commit", base_branch)
                if diff.count('\n') > 4:
                    # Empty diff, this is a null-merge
                    repo.git.apply("--index", name_diff)
                repo.git.commit("-F", name_msg)

        base_branch = next_branch


def rebase(conf, param_handler, args):
    param_handler.add_topic_arg()
    param_handler.add_topic_arg()
    param_handler.add_boolean_arg("gca")
    ctx = param_handler.parse(args)

    if ctx.gca:
        # Convert existing topic branches to GCA
        descending_series = conf.series[:]
        descending_series.sort()
        up_version = descending_series.pop()
        while descending_series:
            next_version = descending_series.pop()
            print("Rebasing topic for " + next_version)

            repo = git.Repo("topics/"+ctx.topic+"/"+next_version)

            topic_branch = "ps-" + next_version + "-" + ctx.topic
            topic_refs = repo.git.rev_list(topic_branch,
                                           "^" + next_version,
                                           "--first-parent",
                                           "--topo-order").split('\n')
            if len(topic_refs) > 1:
                print(topic_refs)
                # Supporting more commits would require some kind of
                # error-handling/continuation stuff
                print("Error: rebase assumes there's only one feature commit")
                return

            missing_refs = repo.git.rev_list(next_version,
                                             "^" + up_version,
                                             "--first-parent",
                                             "--topo-order")
            first_ref = missing_refs.split('\n')[-1]
            up_version = first_ref
            repo.git.reset("--hard", first_ref + "^")
            if topic_refs[0] != '':
                repo.git.cherry_pick(topic_refs[0])


def print_help():
    # Print a usage message
    __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                    os.path.dirname(__file__)))
    print(open(__location__ + "/help.txt").read())


def mbt_command():

    if len(sys.argv) < 2:
        print_help()
        return

    root = MbtRoot()
    conf = import_config(root)
    ctx = DirectoryContext(conf, root.root_dir(), os.getcwd())
    param_handler = MbtParams(conf, ctx, prog_name="mbt " + sys.argv[1])

    os.chdir(root.root_dir())

    repo = repo_object(conf)

    if sys.argv[1] == "init":
        init_mbt(conf, repo)
        return

    if sys.argv[1] == "pull-series":
        run_pull(repo, param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "push-series":
        run_push(conf)
        return

    if sys.argv[1] == "create-topic":
        create_topic(repo, param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "create-build":
        create_build(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "delete-build":
        delete_build(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "make":
        build_with(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "install":
        install_build(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "run-mysqld":
        run_mysqld(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "run-mysql-cmd":
        exec_local_mysql(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "run-bash":
        run_local_bash(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "exec-bash":
        exec_local_bash(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "mtr":
        test_with_mtr(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "asan-symbolize":
        asan_symbolize(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "cleanup":
        cleanup_repo(conf, len(sys.argv) >= 3 and sys.argv[2] == "--force")
        return

    if sys.argv[1] == "reupmerge":
        reupmerge(param_handler, sys.argv[2:])
        return

    if sys.argv[1] == "rebase":
        rebase(conf, param_handler, sys.argv[2:])
        return

    print_help()
