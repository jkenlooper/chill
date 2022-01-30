# syntax=docker/dockerfile:1.3.0-labs

FROM alpine:3.15.0@sha256:21a3deaa0d32a8057914f36584b5288d2e5ecc984380bc0118285c70fa8c9300 as build

LABEL org.opencontainers.image.authors="Jake Hickenlooper <jake@weboftomorrow.com>"


## Build dependencies
WORKDIR /usr/local/src/chill-venv
COPY requirements.txt ./
RUN <<BUILD_DEPENDENCIES
apk update
apk add --no-cache \
  gcc \
  python3 \
  python3-dev \
  libffi-dev \
  build-base \
  musl-dev
ln -s /usr/bin/python3 /usr/bin/python
python -m venv .
/usr/local/src/chill-venv/bin/pip install --upgrade pip wheel
/usr/local/src/chill-venv/bin/pip install --disable-pip-version-check --compile -r requirements.txt
apk --purge del \
  gcc \
  python3-dev \
  libffi-dev \
  build-base \
  musl-dev
BUILD_DEPENDENCIES

COPY . ./
RUN <<CHILL
set -o errexit
/usr/local/src/chill-venv/bin/pip install --disable-pip-version-check --compile .
/usr/local/src/chill-venv/bin/python src/chill/tests.py
ln -s /usr/local/src/chill-venv/bin/chill /usr/local/bin/chill
export PATH=/usr/local/bin:$PATH
/usr/local/bin/chill --version
CHILL

## Stage 2

FROM alpine:3.15.0@sha256:21a3deaa0d32a8057914f36584b5288d2e5ecc984380bc0118285c70fa8c9300

WORKDIR /usr/local/src/
COPY --from=build /usr/local/src/chill-venv /usr/local/src/chill-venv

ENV PATH=/usr/local/bin:$PATH

ARG CHILL_DATABASE_URI=/var/lib/chill/sqlite3/db
ENV CHILL_DATABASE_URI=$CHILL_DATABASE_URI

RUN <<CHILL_DEPENDENCIES
apk update
apk add --no-cache \
  python3 \
  sqlite
ln -s /usr/bin/python3 /usr/bin/python
ln -s /usr/local/src/chill-venv/bin/chill /usr/local/bin/chill
addgroup -g 2000 chill
adduser -u 2000 -G chill -s /bin/sh -D chill
# Create directory where running chill app source files will be.
mkdir -p /home/chill/app
chown -R chill:chill /home/chill
# Create directory where running chill app database will be.
mkdir -p /var/lib/chill/sqlite3
chown -R chill:chill /var/lib/chill
CHILL_DEPENDENCIES

USER chill
WORKDIR /home/chill/app

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

# Default port for chill application is 5000
EXPOSE 5000

ENTRYPOINT ["/usr/local/src/chill-venv/bin/chill"]

CMD ["--help"]

## Build and run example.
# DOCKER_BUILDKIT=1 docker build -t chill:latest .
# docker run -it --rm \
#   -p 8080:5000 \
#   --mount "type=volume,src=chill_app_example,dst=/home/chill/app" \
#   --mount "type=volume,src=chill_db_example,dst=/var/lib/chill/sqlite3" \
#   chill:latest
