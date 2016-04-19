#!/bin/bash

SCRIPT_NAME="$0"
SCRIPTS_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LIB_DIR="${SCRIPTS_ROOT}/lib/"

export PYTHONPATH=${LIB_DIR}:${PYTHON_PATH}
PYTHON="$(which python3)"

echo -e "[${SCRIPT_NAME}] start dime"
${PYTHON} -m app.camera_dime $1 $2 $3 $4

echo -e "[${SCRIPT_NAME}] exit"
