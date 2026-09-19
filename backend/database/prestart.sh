#!/usr/bin/env bash

set -e

export PYTHONPATH=$PYTHONPATH:$(pwd)

cd database
alembic upgrade head
echo "Migrations applied!"
cd ..

exec "$@"