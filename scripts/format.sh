#!/bin/sh -e
set -x

ruff sgpt tests scripts --fix
black sgpt tests scripts
isort sgpt tests scripts
