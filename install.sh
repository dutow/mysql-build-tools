#!/bin/bash

if ! [ -x pipenv ]; then
  echo "pipenv is not available, install it first."
  echo "on ubuntu: apt install pipenv"
  exit 1
fi

if ! [ -x docker ]; then
  echo "docker is not available."
  echo "You should create the mbt network later using:"
  echo "docker network create mbt"
fi

cd ~
git clone https://github.com/dutow/mysql-build-tools.git
echo "export PATH=\$PATH:`pwd`/mysql-build-tools/bin" >> ~/.profile
cd mysql-build-tools
PIPENV_PIPFILE="`pwd`/bin/../Pipfile" pipenv install --python 3
if [ -x docker ]; then
  docker network create mbt
fi
echo "==========================="
echo "MBT installed. Now:"
echo " * Initialize mbt:"
echo "   mkdir workspace"
echo "   cd workspace"
echo "   cp ~/mysql-build-tools/mbt_config.py.sample mbt_config.py"
echo "   mbt init"
