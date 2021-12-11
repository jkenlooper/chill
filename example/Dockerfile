# syntax=docker/dockerfile:1.3.0-labs

from chill

WORKDIR /home/chill/app

COPY . ./
RUN <<APP
chill initdb || printf ''
chill load --yaml chill-data.yaml || printf ''
APP

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

CMD ["chill", "serve"]
