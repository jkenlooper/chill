# syntax=docker/dockerfile:1.4.1

FROM python:3.9-buster

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
/usr/src/chill-venv/bin/pip install --disable-pip-version-check --compile -r requirements.txt

# Create an unprivileged user.
adduser chill --disabled-login --disabled-password --gecos ""
INSTALL

# Install chill
WORKDIR /usr/src/chill
COPY . .
RUN <<CHILL
set -o errexit
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

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

CMD ["/usr/local/src/chill-venv/bin/python", "/usr/local/src/chill-venv/src/chill/tests.py"]
