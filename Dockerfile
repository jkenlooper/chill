# syntax=docker/dockerfile:1.4.3

# UPKEEP due: "2023-04-21" label: "Alpine Linux base image" interval: "+3 months"
# docker pull alpine:3.17.1
# docker image ls --digests alpine
FROM alpine:3.17.1@sha256:f271e74b17ced29b915d351685fd4644785c6d1559dd1f2d4189a5e851ef753a

LABEL org.opencontainers.image.authors="Jake Hickenlooper <jake@weboftomorrow.com>"

RUN <<DEV_USER
# Create dev user
set -o errexit
addgroup -g 44444 dev
adduser -u 44444 -G dev -s /bin/sh -D dev
DEV_USER

# The chill user is created mostly for backwards compatibility
RUN <<CHILL_USER
# Create chill user
set -o errexit
addgroup -g 2000 chill
adduser -u 2000 -G chill -s /bin/sh -D chill
# Create directory where running chill app database will be.
mkdir -p /var/lib/chill/sqlite3
chown -R chill:chill /var/lib/chill
CHILL_USER

WORKDIR /home/dev/app

RUN <<PACKAGE_DEPENDENCIES
# apk add package dependencies
set -o errexit
apk update
apk add --no-cache \
  -q --no-progress \
  gcc \
  sqlite \
  python3 \
  python3-dev \
  py3-pip \
  py3-yaml \
  libffi-dev \
  build-base \
  musl-dev

expected_python_version="Python 3.10.10"
actual_python_version="$(python -V)"
set -x; test "$actual_python_version" = "$expected_python_version"; set +x
PACKAGE_DEPENDENCIES

RUN  <<PYTHON_VIRTUALENV
# Setup for python virtual env
set -o errexit
mkdir -p /home/dev/app
chown -R dev:dev /home/dev/app
su dev -c '/usr/bin/python3 -m venv /home/dev/app/.venv'
PYTHON_VIRTUALENV
# Activate python virtual env by updating the PATH
ENV VIRTUAL_ENV=/home/dev/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --chown=dev:dev pip-requirements.txt /home/dev/app/pip-requirements.txt
COPY --chown=dev:dev dep /home/dev/app/dep

USER dev

RUN <<PIP_INSTALL
# Install pip-requirements.txt
set -o errexit
# Install these first so packages like PyYAML don't have errors with 'bdist_wheel'
python -m pip install wheel
python -m pip install pip
python -m pip install hatchling
python -m pip install \
  --no-index \
  --no-build-isolation \
  --find-links /home/dev/app/dep/ \
  -r /home/dev/app/pip-requirements.txt
PIP_INSTALL

COPY --chown=dev:dev requirements.txt /home/dev/app/requirements.txt
COPY --chown=dev:dev requirements-cli.txt /home/dev/app/requirements-cli.txt
COPY --chown=dev:dev requirements-dev.txt /home/dev/app/requirements-dev.txt
COPY --chown=dev:dev requirements-test.txt /home/dev/app/requirements-test.txt
COPY --chown=dev:dev pyproject.toml /home/dev/app/pyproject.toml
COPY --chown=dev:dev src/chill/_version.py /home/dev/app/src/chill/_version.py
COPY --chown=dev:dev README.md /home/dev/app/README.md
COPY --chown=dev:dev COPYING /home/dev/app/
COPY --chown=dev:dev COPYING.LESSER /home/dev/app/
RUN <<PIP_INSTALL_APP
# Install the local python packages.
set -o errexit

# Only pip install with the local python packages cache.
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -r /home/dev/app/requirements.txt
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -r /home/dev/app/requirements-cli.txt
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -r /home/dev/app/requirements-dev.txt
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  -r /home/dev/app/requirements-test.txt
PIP_INSTALL_APP

COPY --chown=dev:dev src /home/dev/app/src
RUN <<INSTALL_CHILL
# Install chill
set -o errexit
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  /home/dev/app
python src/chill/tests.py
chill --version
INSTALL_CHILL

ARG CHILL_DATABASE_URI=/var/lib/chill/sqlite3/db
ENV CHILL_DATABASE_URI=$CHILL_DATABASE_URI

USER chill

WORKDIR /home/chill/app

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

# Default port for chill application is 5000
EXPOSE 5000

ENTRYPOINT ["chill"]

CMD ["--help"]

## Build and run example.
# DOCKER_BUILDKIT=1 docker build -t chill:latest .
# docker run -it --rm \
#   -p 8080:5000 \
#   --mount "type=volume,src=chill_app_example,dst=/home/chill/app" \
#   --mount "type=volume,src=chill_db_example,dst=/var/lib/chill/sqlite3" \
#   chill:latest
