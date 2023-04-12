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

if black ./sgpt ./tests --check --target-version py310
then
    echo 'Black passed ✅'
else
    echo 'Black failed ❌'
    echo 'RUN: black ./sgpt ./tests --target-version py310'
    exit 1
fi

if pylint \
  ./sgpt \
  ./tests \
  --disable=fixme \
  --disable=cyclic-import \
  --disable=useless-import-alias \
  --disable=missing-function-docstring \
  --disable=missing-module-docstring \
  --disable=missing-class-docstring \
  --disable=too-many-function-args
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
