# syntax=docker/dockerfile:1.3.0-labs

from chill:latest

WORKDIR /home/chill/app

COPY --chown=chill:chill site.cfg chill-data.yaml ./
RUN <<APP
chill initdb || printf ''
chill load --yaml chill-data.yaml || printf ''
APP

COPY --chown=chill:chill . ./

CMD ["chill", "serve"]
