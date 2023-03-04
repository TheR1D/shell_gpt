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

if black --exclude venv --check --target-version py310 -l 120 *.py
then
    echo 'Black passed ✅'
else
    echo 'Black failed ❌'
    echo 'RUN: black --exclude venv --target-version py310 -l 120 *.py'
    exit 1
fi

if pylint \
  *.py \
  --disable=missing-function-docstring \
  --disable=too-many-arguments \
  --disable=missing-module-docstring \
  --disable=import-error \
  --disable=missing-class-docstring \
  --disable=too-many-instance-attributes \
  --disable=too-many-function-args \
  --disable=unspecified-encoding \
  --max-line-length=120 \
  --ignore=venv
then
    echo 'Pylint passed ✅'
else
    echo 'Pylint failed ❌'
    exit 1
fi

if python -m unittest tests/unittests.py
then
  echo 'Unittests passed ✅'
else
    echo 'Unittests failed ❌'
    exit 1
fi

echo 'Well done.'
