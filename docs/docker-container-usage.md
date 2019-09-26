# Example Docker Usage

Disclaimer: I am not actively maintaining or using chill in a docker container.

Chill can also be run as a docker container.  Build it using the Dockerfile
located here.  The chill image sets the `ENTRYPOINT` to be the chill command and
copies the context to the container so you can use `docker run` commands to work
with chill like it was installed on the host machine.

These are just some example commands to give an idea on how to do development
with a container.  In all of them the `--rm` is being used since there is no
need to keep the container around after the command finishes.  The `-v` option
is to allow the working directory to be bind-mounted to the host.  It should
contain all the normal files for chill including the sqlite3 database.

Also note that when developing it like this the chill app won't be directly
accessible under the PORT set in `site.cfg`.  In the example commands I set the
port mapping (`-p 8080:5000`).  It will need to have it's `site.cfg` `HOST`
updated to be '0.0.0.0' or have some other kind of networking setup.

### Start in the foreground.

This is equivalent to using `chill run` within `$HOME/example-website/`, but
maps the port from 8080 on the host to port 5000 for the chill app.  Then you
can visit the website via http://localhost:8080 which will be running in
a docker container.  You will need to make sure that the `site.cfg` has been
updated to set the HOST to be external (0.0.0.0), or you won't be able to hit
it with your web browser.

```bash
docker run --rm -p 8080:5000 -v $HOME/example-website/:/usr/run/ chill run
```

### Serve the app in daemon mode

Same as using `chill serve`.  Uses the `-d` option for running the container in
the background.

```bash
docker run -d --rm -p 8080:5000 -v $HOME/example-website/:/usr/run/ chill serve
```

### Run operate sub command

Same as using `chill operate`.  Here the `-it` option is used so the operate
functions correctly since it needs user input.

```bash
docker run -it --rm -v $HOME/example-website/:/usr/run/ chill operate
```
