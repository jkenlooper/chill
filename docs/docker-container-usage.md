# Example Docker Usage

Build chill image and tag it to latest.

```bash
DOCKER_BUILDKIT=1 docker build -t chill:latest .
```

Create the example app with `chill init` command which will create the initial
database tables and add the example content to them. The two volumes are created
here to hold the data for the app.

```bash
docker run -it --rm \
  --mount "type=volume,src=chill_app_example,dst=/home/chill/app" \
  --mount "type=volume,src=chill_db_example,dst=/var/lib/chill/sqlite3" \
  chill:latest init
```

Start the chill app in the foreground when developing. The `chill run` command
is used for this as it will output any debugging information and should auto
reload if some files change. Don't use `chill run` for production. The chill app
will be accessible at http://localhost:8080/ .

```bash
docker run -it --rm \
  -p 8080:5000 \
  --mount "type=volume,src=chill_app_example,dst=/home/chill/app" \
  --mount "type=volume,src=chill_db_example,dst=/var/lib/chill/sqlite3" \
  chill:latest run
```

Or replace the entrypoint with `sh` and try the `chill` app that way.

```bash
docker run -it --rm \
  -p 8080:5000 \
  --mount "type=volume,src=chill_app_example,dst=/home/chill/app" \
  --mount "type=volume,src=chill_db_example,dst=/var/lib/chill/sqlite3" \
  --entrypoint=/bin/sh \
  chill:latest
```
