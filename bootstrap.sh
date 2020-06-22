#!/usr/bin/env bash

# This script creates a virtual Python environment in ./python-env with all required libraries set up.
# To use it, call Python at ./python-env/bin/python.

# Test if everything is available
python3 --version >/dev/null 2>&1 || missing=$missing"[bootstrap.sh] Python3 is required but it's not installed.\n"
virtualenv --version >/dev/null 2>&1 || missing=$missing"[bootstrap.sh] Python virtualenv is required but it's not installed.\n"
gcc --version >/dev/null 2>&1 || missing=$missing"[bootstrap.sh] GCC is required but it's not installed.\n"
git --version >/dev/null 2>&1 || missing=$missing"[bootstrap.sh] GIT is required but it's not installed.\n"


# Report errors if any
if [[ -n "$missing" ]]; then
    echo -e ${missing%\\n}
    echo "[bootstrap.sh] Please install missing programs."
    exit 1
fi

## find python3 interpreter

pypath=`which python3`
virtualenv --python=$pypath python_env
./python_env/bin/pip install pyyaml numpy biopython psutil cpython scipy deepdiff tqdm
