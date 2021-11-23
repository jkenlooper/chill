# syntax=docker/dockerfile:1

FROM python:3.10.0-buster
#FROM python:3.8.10-buster

LABEL maintainer="Jake Hickenlooper jake@weboftomorrow.com"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get --yes update \
  && apt-get --yes upgrade \
  && apt-get --yes install --no-install-suggests --no-install-recommends \
  gcc \
  libffi-dev \
  libpython3-dev \
  libsqlite3-dev \
  python3-dev \
  python3-venv \
  sqlite3

# Virtual environment
WORKDIR /usr/src/chill-venv
COPY requirements.txt ./
RUN python -m venv .
RUN /usr/src/chill-venv/bin/pip install --upgrade pip wheel
RUN /usr/src/chill-venv/bin/pip install --disable-pip-version-check -r requirements.txt

# Install chill
WORKDIR /usr/src/chill
VOLUME /usr/src/chill/src/chill
COPY . .
RUN /usr/src/chill-venv/bin/pip install --disable-pip-version-check --compile .
#RUN /usr/src/chill-venv/bin/python src/chill/tests.py



# Create an unprivileged user.
RUN adduser chill --disabled-login --disabled-password --gecos ""

WORKDIR /home/chill/app
RUN chown -R chill:chill /home/chill/app
USER chill
RUN /usr/src/chill-venv/bin/chill init
RUN /usr/src/chill-venv/bin/chill dump --yaml chill-data.yaml
# TODO set HOST=0.0.0.0

EXPOSE 5000
VOLUME /home/chill/app
#docker run -it --rm --mount "type=bind,src=$(pwd)/other,dst=/home/chill/app" chill

#RUN /usr/src/chill-venv/bin/chill init
#RUN /usr/src/chill-venv/bin/chill dump --yaml chill-data.yaml

ENTRYPOINT ["/usr/src/chill-venv/bin/chill"]
CMD ["serve"]
