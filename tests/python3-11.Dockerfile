# syntax=docker/dockerfile:1.4.3

FROM python:3.11-buster

ARG DEBIAN_FRONTEND=noninteractive

RUN <<CHILL_USER
# Create chill user
set -o errexit
adduser chill --disabled-login --disabled-password --gecos ""
CHILL_USER

WORKDIR /home/chill

# UPKEEP due: "2023-03-23" label: "Python pip" interval: "+3 months"
# https://pypi.org/project/pip/
ARG PIP_VERSION=22.3.1
# UPKEEP due: "2023-03-23" label: "Python wheel" interval: "+3 months"
# https://pypi.org/project/wheel/
ARG WHEEL_VERSION=0.38.4
# UPKEEP due: "2023-03-23" label: "Python Cython" interval: "+3 months"
# https://pypi.org/project/Cython/
ARG CYTHON_VERSION=0.29.32
# UPKEEP due: "2023-03-23" label: "Python gunicorn" interval: "+3 months"
# https://pypi.org/project/gunicorn/
ARG GUNICORN_VERSION="20.1.0"

RUN <<BUILD_DEPENDENCIES
# Install build dependencies
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

expected_python_version="Python 3.11.1"
actual_python_version="$(python -V)"
set -x; test "$actual_python_version" = "$expected_python_version"; set +x

# Only download to a directory to allow the pip install to happen later with
# a set --find-links option.
python -m pip download \
  --disable-pip-version-check \
  --destination-directory /var/lib/chill/python \
  gunicorn[setproctitle]=="$GUNICORN_VERSION" \
  pip=="$PIP_VERSION" \
  wheel=="$WHEEL_VERSION" \
  Cython=="$CYTHON_VERSION" \
  Frozen-Flask>=0.18 \
  docopt>=0.6.2
BUILD_DEPENDENCIES

COPY requirements.txt /home/chill/requirements.txt
RUN <<PIP_DOWNLOAD_REQS
# Download Python packages listed in requirements.txt
set -o errexit
python -m pip download \
  --disable-pip-version-check \
  --destination-directory /var/lib/chill/python \
  -r /home/chill/requirements.txt
PIP_DOWNLOAD_REQS

RUN  <<PYTHON_VIRTUALENV
# Setup for python virtual env
set -o errexit
mkdir -p /home/chill/app
mkdir -p /usr/local/src/chill-venv
python -m venv /usr/local/src/chill-venv
# The chill user will need write access since pip install will be adding files to
# the chill-venv directory.
chown -R chill:chill /usr/local/src/chill-venv
PYTHON_VIRTUALENV
# Activate python virtual env by updating the PATH
ENV VIRTUAL_ENV=/usr/local/src/chill-venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN <<PIP_INSTALL
# Install downloaded Python packages
set -o errexit
python -m pip install \
  --disable-pip-version-check \
  --no-index --find-links /var/lib/chill/python \
  pip \
  wheel \
  Cython \
  gunicorn[setproctitle] \
  Frozen-Flask \
  docopt
python -m pip install \
  --disable-pip-version-check \
  --no-index --find-links /var/lib/chill/python \
  -r /home/chill/requirements.txt
PIP_INSTALL

WORKDIR /home/chill/app
COPY --chown=chill:chill COPYING /home/chill/app/
COPY --chown=chill:chill COPYING.LESSER /home/chill/app/
COPY --chown=chill:chill setup.py /home/chill/app/
COPY --chown=chill:chill README.md /home/chill/app/
COPY --chown=chill:chill src/chill /home/chill/app/src/chill

RUN <<INSTALL_CHILL
# Install chill
set -o errexit
python -m pip install \
  --disable-pip-version-check \
  --no-index --find-links /var/lib/chill/python \
  --compile .
python src/chill/tests.py
chill --version
INSTALL_CHILL


ARG CHILL_DATABASE_URI=/var/lib/chill/sqlite3/db
ENV CHILL_DATABASE_URI=$CHILL_DATABASE_URI

RUN <<CHILL_SETUP
# Setup chill
set -o errexit
# Create directory where running chill app database will be.
mkdir -p /var/lib/chill/sqlite3
chown -R chill:chill /var/lib/chill
chown -R chill:chill /home/chill
CHILL_SETUP

USER chill

RUN <<EXAMPLE
# Example of chill init and dump
set -o errexit
chill init
chill dump --yaml chill-data.yaml
EXAMPLE

EXPOSE 5000

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

ENTRYPOINT ["/usr/local/src/chill-venv/bin/chill"]

CMD ["--help"]
