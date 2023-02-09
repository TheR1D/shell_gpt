#!/usr/bin/env bash

chmod +x "$PWD/pre-push.sh"
ln -sf "$PWD/pre-push.sh" .git/hooks/pre-push

# Check if pylint is installed
if ! command -v pylint > /dev/null; then
    echo "pylint is not installed. Install it with 'pip install pylint'"
    exit 1
fi

# Check if black is installed
if ! command -v black > /dev/null; then
    echo "black is not installed. Install it with 'pip install black'"
    exit 1
fi

echo 'Executing pre-push hook.'

if [ -f "$PWD/venv/bin/activate" ]; then
    source $PWD/venv/bin/activate
fi

if black --check --target-version py310 -l 120 sgpt.py
then
    echo 'Black passed ✅'
else
    echo 'Black failed ❌'
    echo 'RUN: black --target-version py310 -l 120 sgpt.py'
    exit 1
fi

if pylint sgpt.py
then
    echo 'Pylint passed ✅'
else
    echo 'Pylint failed ❌'
    exit 1
fi

echo 'Well done.'