# syntax=docker/dockerfile:1.3.0-labs

FROM python:3.10.0-buster
#FROM python:3.8.10-buster

LABEL maintainer="Jake Hickenlooper jake@weboftomorrow.com"

ARG DEBIAN_FRONTEND=noninteractive

# Virtual environment
WORKDIR /usr/src/chill-venv

# Install chill dependencies
COPY requirements.txt ./
RUN <<INSTALL
apt-get --yes update
apt-get --yes upgrade
apt-get --yes install --no-install-suggests --no-install-recommends \
  gcc \
  libffi-dev \
  libpython3-dev \
  libsqlite3-dev \
  python3-dev \
  python3-venv \
  sqlite3

python -m venv .
/usr/src/chill-venv/bin/pip install --upgrade pip wheel
/usr/src/chill-venv/bin/pip install --disable-pip-version-check -r requirements.txt

# Create an unprivileged user.
adduser chill --disabled-login --disabled-password --gecos ""
INSTALL

# Install chill
WORKDIR /usr/src/chill
COPY . .
RUN <<CHILL
/usr/src/chill-venv/bin/pip install --disable-pip-version-check --compile .
/usr/src/chill-venv/bin/python src/chill/tests.py
mkdir -p /home/chill/app
chown -R chill:chill /home/chill/app
CHILL

WORKDIR /home/chill/app
USER chill
RUN <<EXAMPLE
/usr/src/chill-venv/bin/chill init
/usr/src/chill-venv/bin/chill dump --yaml chill-data.yaml
EXAMPLE

EXPOSE 5000

VOLUME /home/chill/app

ENTRYPOINT ["/usr/src/chill-venv/bin/chill"]
CMD ["serve"]