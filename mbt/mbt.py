
import git
import sys
import os
import shutil


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


def init_mbt(repo):
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
    for name, url in conf.remotes.items():
        print("Adding remote '" + name + "': " + url)
        ref = repo.create_remote(name, url)
        ref.fetch()


def create_topic(repo, name, versions):
    for ver in versions:
        branch = "ps-"+ver+"-"+name
        add_worktree(repo, "topics/"+name+"/"+ver, branch, ver)


def run_docker_command(img, volumes, work_dir, env, args):

    def proc_volume_arg(v):
        curr_dir = os.getcwd()
        a = v.split(":")
        if len(a) == 1:
            a.append(a[0])
        if a[0][0] != '/':
            a[0] = curr_dir + "/" + a[0]
            a[1] = "/work/" + a[1]
        return "-v" + a[0] + "/:" + a[1]

    volumes = list(map(proc_volume_arg, volumes))

    def proc_env_arg(v):
        return ["-e", v[0]+"="+v[1]]

    env = sum(list(map(proc_env_arg, env.items())), [])

    docker_args = (["/urs/bin/docker", "run", "--privileged", "--rm", "-it"]
                   + volumes
                   + env
                   + ["-w", work_dir]
                   + [img]
                   + args
                   )

    print(docker_args)

    os.execvp("/usr/bin/docker",
              docker_args
              )


def run_docker_build_command(conf, topic, version, preset, work_dir, args):
    src_dir = os.path.join("topics", topic, version)
    build_dir = os.path.join("topics", topic, version+"-"+preset)

    if not os.path.isdir(build_dir):
        os.mkdir(build_dir)

    buildconf = conf.build_configs[preset]

    volumes = [src_dir+":src",
               build_dir+":build",
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


conf = import_config()
repo = repo_object(conf)

if sys.argv[1] == "init":
    init_mbt(repo)

if sys.argv[1] == "create-topic":
    create_topic(repo, sys.argv[2], conf.versions)

if sys.argv[1] == "create-build":
    create_build(conf, sys.argv[2], sys.argv[3], sys.argv[4])

if sys.argv[1] == "delete-build":
    delete_build(conf, sys.argv[2], sys.argv[3], sys.argv[4])

if sys.argv[1] == "make":
    build_with_make(conf, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])

if sys.argv[1] == "mtr":
    test_with_mtr(conf, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
