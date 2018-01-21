#!/bin/bash

git clone https://github.com/dutow/mysql-build-tools.git
ln -s mysql-build-tools/bin/mbt mbt
PIPENV_PIPFILE="`pwd`/mysql-build-tools/Pipfile" pipenv install --python 3.6
echo "==========================="
echo "MBT installed. Now:"
echo " * Create a config file, for example by executing:"
echo "   cp mysql-build-tools/config.py.sample config.py"
echo "   Or you can create one by hand, or customize it"
echo " * Initialize mbt:"
echo "   ./mbt init"
