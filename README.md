MySQL Build Tools
===

[![Build Status](https://travis-ci.org/dutow/mysql-build-tools.svg?branch=master)](https://travis-ci.org/dutow/mysql-build-tools)

Building and testing MySQL is challanging for several reasons:

* There are multiple upstreams (MySQL, Percona, developer forks)
* There are multiple series under active development (5.5, 5.6, 5.7, 8.0)
* It has to be tested with several platforms, compilers, and build configurations

This tool aims to help with some of the above.

The idea
---

* Multiple checkouts of a single git repository using git subtree
* Tools for creating multiple build configs for any checkout
* Running everything using docker, to support any linux distribution / configuration
* Everything should be configurable using a python DSL

The specifics
---

* There is one bare git repo called the master
* There is a checkout for each series truck
* There are topics for development
* Each topic has a checkout of every relevant series
* There can be any number of build configs for any checkout
* Build configs are managed using variants (presets)

Warning
---

This is a highly experimental, mostly undocumented prototype.

Planned features
---

* Logging everything in a structured manner
* Providing a better console command (e.g. working directory awareness)
* Providing a console

Quick start
---

```bash
# NOTE: this installs mbt in ~/mysql-build-tools and adds it to the user's path,
# no matter from where it's called
\curl -sSL https://raw.githubusercontent.com/dutow/mysql-build-tools/master/install.sh | bash -s

mkdir workspace
cd workhspace
cp ~/mysql-build-tools/config.py.sample config.py
mbt init
```

Usage
---

### Create a new topic

```
mbt create-topic -t <name>
```

### Create a new build configuration

```
mbt create-build -t <topic> -s <series> -v <variant> -- [additional args...]
```

This command invokes CMake.

Additional arguments are not yet supported.

### Delete a build configuration

```
mbt delete-build -t <topic> -s <series> -v <variant>
```

Removes the given build directory.

### Building with make

```
mbt make -t <topic> -s <series> -v <variant> -- [additional args...]
```

Any argument can be specified to make, e.g. targets, `-j`, `VERBOSE=1`, ...

### Running the mtr tests

```
mbt mtr -t <topic> -s <series> -v <variant> -- [additional args...]
```

### Cleaning up old branches

```
mbt cleanup [--force]
```

Prunes worktrees and removes branches that aren't checked out.
The `--force` option removes brances even when they have non merged changes.

Note that change detection looks buggy with git worktrees, so if the command reports that a branch has underged changes,
it could be a false positive.
Any argument can be specified to mtr, e.g. `--parallel=auto`, `--force`, ...
