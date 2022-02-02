# syntax=docker/dockerfile:1.3.0-labs

from chill:latest

WORKDIR /home/chill/app

COPY --chown=chill:chill . .
RUN <<APP
# Remove the sqlite3 database file if it exists.
rm -rf "${CHILL_DATABASE_URI}"

# initdb is used to create the initial database tables.
chill initdb

# The load subcommand will populate the database tables with the chill-data.yaml
# contents.
chill load --yaml chill-data.yaml
APP

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

CMD ["serve"]

# DOCKER_BUILDKIT=1 docker build -t chillexample .
# docker run -it --rm -p 8080:5000 chillexample
