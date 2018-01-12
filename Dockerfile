# TODO: use a lighter weight base image
FROM ubuntu:16.04

LABEL maintainer="Jake Hickenlooper jake@weboftomorrow.com"

RUN apt-get update && apt-get --yes install python python-dev python-pip

RUN apt-get --yes install sqlite3 python-sqlite

WORKDIR /usr/src/app

# install chill
ADD . .
RUN pip install .

# Copy the context files to arbitrary /usr/run directory
WORKDIR /usr/run
COPY . .

ENTRYPOINT ["chill"]
