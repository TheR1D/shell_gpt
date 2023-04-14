#!/usr/bin/env bash

set -e
set -x

mypy sgpt
ruff sgpt tests scripts
black sgpt tests --check
isort sgpt tests scripts --check-only
