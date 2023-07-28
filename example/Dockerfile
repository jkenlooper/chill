# syntax=docker/dockerfile:1.4.3

from chill:latest

WORKDIR /home/chill/app

COPY --chown=chill:chill . .

VOLUME /var/lib/chill/sqlite3
VOLUME /home/chill/app

CMD ["serve"]

# DOCKER_BUILDKIT=1 docker build -t chillexample .
# docker run -it --rm -p 8080:5000 chillexample
