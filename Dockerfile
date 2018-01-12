FROM alpine:3.7

LABEL maintainer="Jake Hickenlooper jake@weboftomorrow.com"

RUN apk add --no-cache g++
RUN apk add --no-cache python python-dev

# Install python pip
WORKDIR /usr/src/pip
ADD https://bootstrap.pypa.io/get-pip.py /usr/src/pip/
RUN python get-pip.py --no-wheel

# Install sqlite
RUN apk add --no-cache sqlite

WORKDIR /usr/src/app

# Install chill
ADD . .
RUN pip install .

# Copy the context files to arbitrary /usr/run directory
WORKDIR /usr/run
COPY . .

ENTRYPOINT ["chill"]
