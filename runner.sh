#!/bin/bash

SCRIPT_NAME="$0"
SCRIPTS_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LIB_DIR="${SCRIPTS_ROOT}/lib/"

# virtualenv setup
if [ ! -z ${VIRTUALENV_CFG+x} ]; then
    echo "[${SCRIPT_NAME}] configure virtualenv using file ${VIRTUALENV_CFG}"
    virtualenv /tmp/venv
    source /tmp/venv/bin/activate
    pip3 install -r ${VIRTUALENV_CFG}

    [ $? -eq 0 ] || (echo -e "[${SCRIPT_NAME}] problems with virtualenv setup, exit immediately"; exit 1)
fi
[ $? == 1 ] && exit 0;

export PYTHONPATH=${LIB_DIR}:${PYTHON_PATH}
PYTHON="$(which python3)"

echo -e "[${SCRIPT_NAME}] start dime"
${PYTHON} -m ${APP} $@

echo -e "[${SCRIPT_NAME}] exit"
