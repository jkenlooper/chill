from __future__ import absolute_import
import tempfile

from .database import *
from .app import make_app, db

tmp_db = tempfile.NamedTemporaryFile(delete=False)
app = make_app(CHILL_DATABASE_URI='sqlite:///' + tmp_db.name, DEBUG=True)

def start():
    app.app_context().push()

def stop():
    app.app_context().pop()
    tmp_db.unlink(tmp_db.name)
