# syntax=docker/dockerfile:1.5.2

# UPKEEP due: "2023-09-03" label: "Alpine Linux base image" interval: "+3 months"
# docker pull alpine:3.18.0
# docker image ls --digests alpine
FROM alpine:3.18.0@sha256:02bb6f428431fbc2809c5d1b41eab5a68350194fb508869a33cb1af4444c9b11

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

ARG EXPECTED_PYTHON_VERSION="Python 3.11.3"
RUN <<PACKAGE_DEPENDENCIES
# Install package dependencies and verify python version
set -o errexit
apk update
apk add --no-cache \
  -q --no-progress \
  gcc \
  sqlite \
  python3 \
  python3-dev \
  py3-pip \
  libffi-dev \
  build-base \
  musl-dev

actual_python_version="$(python -V)"
set -x; test "$actual_python_version" = "$EXPECTED_PYTHON_VERSION"; set +x
PACKAGE_DEPENDENCIES

RUN  <<PYTHON_VIRTUALENV
# Setup for python virtual env
set -o errexit
mkdir -p /home/dev/app
chown -R dev:dev /home/dev/app
su dev -c 'python -m venv /home/dev/app/.venv'
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
actual_python_version="$(python -V)"
set -x; test "$actual_python_version" = "$EXPECTED_PYTHON_VERSION"; set +x
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
