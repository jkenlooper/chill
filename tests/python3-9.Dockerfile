# syntax=docker/dockerfile:1.5.2

FROM python:3.9-buster

ARG DEBIAN_FRONTEND=noninteractive

RUN <<DEV_USER
# Create dev user
set -o errexit
adduser dev --disabled-login --disabled-password --gecos ""
DEV_USER

RUN <<CHILL_USER
# Create chill user
set -o errexit
adduser chill --disabled-login --disabled-password --gecos ""
# Create directory where running chill app database will be.
mkdir -p /var/lib/chill/sqlite3
chown -R chill:chill /var/lib/chill
CHILL_USER

WORKDIR /home/dev/app

ARG EXPECTED_PYTHON_VERSION="Python 3.9.16"
RUN <<PACKAGE_DEPENDENCIES
# Install package dependencies and verify python version
set -o errexit
apt-get --yes update
apt-get --yes upgrade
apt-get --yes install --no-install-suggests --no-install-recommends \
  gcc \
  libffi-dev \
  libpython3-dev \
  libsqlite3-dev \
  python3-dev \
  python3-venv \
  python3-pip \
  sqlite3

mkdir -p /var/lib/chill/python

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
COPY --chown=dev:dev pyproject.toml /home/dev/app/pyproject.toml
COPY --chown=dev:dev src/chill/_version.py /home/dev/app/src/chill/_version.py
# Skip copy of any actual dep/* files, just want an empty directory made
COPY --chown=dev:dev dep/.gitkeep /home/dev/app/dep/.gitkeep
COPY --chown=dev:dev README.md /home/dev/app/README.md

USER dev

RUN <<PIP_DOWNLOAD
# Download python packages listed in pyproject.toml
set -o errexit
actual_python_version="$(python -V)"
set -x; test "$actual_python_version" = "$EXPECTED_PYTHON_VERSION"; set +x

# Install these first so packages like PyYAML don't have errors with 'bdist_wheel'
python -m pip install --upgrade-strategy eager wheel
python -m pip install --upgrade-strategy eager pip
python -m pip install --upgrade-strategy eager hatchling
python -m pip download --disable-pip-version-check \
    --exists-action i \
    --no-build-isolation \
    --find-links /home/dev/app/dep/ \
    --destination-directory /home/dev/app/dep \
    -r /home/dev/app/pip-requirements.txt
python -m pip download --disable-pip-version-check \
    --exists-action i \
    --no-build-isolation \
    --find-links /home/dev/app/dep/ \
    --destination-directory /home/dev/app/dep \
    .[cli,dev,test]
PIP_DOWNLOAD

RUN <<PIP_INSTALL
# Install pip-requirements.txt
set -o errexit
python -m pip install \
  --no-index \
  --no-build-isolation \
  --find-links /home/dev/app/dep/ \
  -r /home/dev/app/pip-requirements.txt
PIP_INSTALL

COPY --chown=dev:dev pyproject.toml /home/dev/app/pyproject.toml
COPY --chown=dev:dev src/chill/_version.py /home/dev/app/src/chill/_version.py
COPY --chown=dev:dev README.md /home/dev/app/README.md
COPY --chown=dev:dev COPYING /home/dev/app/
COPY --chown=dev:dev COPYING.LESSER /home/dev/app/
RUN <<PIP_INSTALL_APP
# Install the local python packages listed in pyproject.toml.
set -o errexit

# Only pip install with the local python packages cache.
python -m pip install --disable-pip-version-check --compile \
  --no-index \
  --no-build-isolation \
  --find-links /home/dev/app/dep/ \
  .[cli,dev,test]
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

RUN <<EXAMPLE
# Example of chill init and dump
set -o errexit
chill init
chill dump --yaml chill-data.yaml
EXAMPLE

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

# Default port for chill application is 5000
EXPOSE 5000

ENTRYPOINT ["chill"]

CMD ["--help"]
