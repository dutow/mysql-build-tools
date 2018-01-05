MySQL Build Tools
===

Building and testing MySQL is challanging for several reasons:

* There are multiple upstreams (MySQL, Percona, developer forks)
* There are multiple versions under active development (5.5, 5.6, 5.7, 8.0)
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
* There is a checkout for each version truck
* There are topics for development
* Each topic has a checkout of every relevant version
* There can be any number of build configs for any checkout
* Build configs are managed using presets

Warning
---

This is a highly experimental, mostly undocumented prototype.

Planned features
---

* Logging everything in a structured manner
* Providing a better console command (e.g. working directory awareness)
* Providing a console

Installation
---

TODO

Usage
---

### Create a new topic

```
./mbt create-topic <name>
```

### Create a new build configuration

```
./mbt create-build <topic> <version> <preset> [additional args...]
```

This command invokes CMake.

Additional arguments are not yet supported.

### Delete a build configuration

```
./mbt delete-build <topic> <version> <preset>
```

Removes the given build directory.

### Building with make

```
./mbt make <topic> <version> <preset> [additional args...]
```

Any argument can be specified to make, e.g. targets, `-j`, `VERBOSE=1`, ...

### Running the mtr tests

```
./mbt mtr <topic> <version> <preset> [additional args...]
```

Any argument can be specified to mtr, e.g. `--parallel=auto`, `--force`, ...
