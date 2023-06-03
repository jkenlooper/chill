#!/usr/bin/env sh

set -o errexit

project_dir="$(dirname "$(dirname "$(realpath "$0")")")"

# TODO It would be better to use a template for the Dockerfiles.

alpine_default="chill:latest"
python3_11="python3.11-buster-chill:latest"
python3_10="python3.10-buster-chill:latest"
python3_9="python3.9-buster-chill:latest"
python3_8="python3.8-buster-chill:latest"

export DOCKER_BUILDKIT=1

# Need to make sure that dep/ directory has packages in it for the
# alpine_default build.
"$project_dir/update-dep.sh"

set -x
docker image rm "$alpine_default" > /dev/null 2>&1 || printf ""
docker build -t "$alpine_default" -f "$project_dir/Dockerfile" "$project_dir"

docker image rm "$python3_11" > /dev/null 2>&1 || printf ""
docker build -t "$python3_11" -f "$project_dir/tests/python3-11.Dockerfile" "$project_dir"

docker image rm "$python3_10" > /dev/null 2>&1 || printf ""
docker build -t "$python3_10" -f "$project_dir/tests/python3-10.Dockerfile" "$project_dir"

docker image rm "$python3_9" > /dev/null 2>&1 || printf ""
docker build -t "$python3_9" -f "$project_dir/tests/python3-9.Dockerfile" "$project_dir"

docker image rm "$python3_8" > /dev/null 2>&1 || printf ""
docker build -t "$python3_8" -f "$project_dir/tests/python3-8.Dockerfile" "$project_dir"
set +x
