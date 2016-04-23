#!/bin/bash

ALL_PY_FILES=$(find ../ -name "*.py")

echo -e "General Vue on a Module"
pyreverse -ASmy -k -o pdf ${ALL_PY_FILES} -p general_vue

echo -e "Detailed Vue on a Module"
# pyreverse -c module_one -a1 -s1 -f ALL -o pdf ${ALL_PY_FILES}

echo -e "Default"
pyreverse -o pdf -p default ${ALL_PY_FILES}

echo -e "Default but with all attributes"
pyreverse -o pdf -p default_all_attributes -f ALL ${ALL_PY_FILES}
