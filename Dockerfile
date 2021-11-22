FROM python:3.10.0-buster
#FROM python:3.8.10-buster

LABEL maintainer="Jake Hickenlooper jake@weboftomorrow.com"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get --yes update \
  && apt-get --yes upgrade

# Create an unprivileged user.
RUN adduser chill --disabled-login --disabled-password --gecos ""

RUN apt-get --yes install gcc python3-dev libsqlite3-dev libffi-dev
#RUN apk add --no-cache python3-dev cython py3-cffi libffi libffi-dev

# Install sqlite
RUN apt-get --yes install sqlite3

RUN pip install --upgrade pip
#RUN pip install Cython
RUN pip install gevent
RUN pip install greenlet

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN chown -R chill:chill /usr/src/app

ENV PATH=$PATH:/home/chill/.local/bin

#RUN python -m venv .
#RUN . bin/activate
RUN pip install -r requirements.txt

# Install chill
COPY . .
RUN pip install -e .
RUN python src/chill/tests.py

WORKDIR /usr/run
RUN chown -R chill:chill /usr/run
USER chill

# chill initdb
# chill load --yaml chill-data.yaml
# chill serve

ENTRYPOINT ["chill"]
