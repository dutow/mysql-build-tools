#!/bin/bash

cd ~
git clone https://github.com/dutow/mysql-build-tools.git
echo "export PATH=\$PATH:`pwd`/mysql-build-tools/bin" >> ~/.bashrc
cd mysql-build-tools
PIPENV_PIPFILE="`pwd`/Pipfile" pipenv install --python 3.6
echo "==========================="
echo "MBT installed. Now:"
echo " * Initialize mbt:"
echo "   mkdir workspace"
echo "   cd workspace"
echo "   cp ~/mysql-build-tools/mbt_config.py.sample mbt_config.py"
echo "   mbt init"
