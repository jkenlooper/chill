#!/usr/bin/env sh

set -o errexit

project_dir="$(dirname "$(dirname "$(realpath "$0")")")"

python3_10="python3.10-buster-chill:latest"
python3_9="python3.9-buster-chill:latest"
python3_8="python3.8-buster-chill:latest"

export DOCKER_BUILDKIT=1
docker build -t "$python3_10" -f "$project_dir/tests/python3-10.Dockerfile" "$project_dir"
docker build -t "$python3_9" -f "$project_dir/tests/python3-9.Dockerfile" "$project_dir"
docker build -t "$python3_8" -f "$project_dir/tests/python3-8.Dockerfile" "$project_dir"

docker image rm "$python3_10"
docker image rm "$python3_9"
docker image rm "$python3_8"

