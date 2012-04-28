import os.path
from mimetypes import guess_type

from flask import abort, redirect, send_file
from flask.views import MethodView

from chill import app

class ResourceView(MethodView):
    """
    A resource is considered anything that does not use a template.
    It will also need an extension and cannot start with a "."
    """

    def get(self, uri, ext):
        """
        get the specified resource
        """
        # check if it exists in data_path

        # a//b == a/b/ == a/./b == a/foo/../b
        # prepend a '/' to fix ../../a/b to /a/b
        modified_uri = os.path.normpath('/%s' % uri)
        modified_uri = modified_uri[1:] # strip the extra '/'

        uri_split = modified_uri.split('/')
        uri_path = os.path.join(*uri_split)
        uri_path = '.'.join((uri_path, ext))
        abs_path = os.path.join(app.config['DATA_PATH'], uri_path)

        #just in case...
        def resource_within_data_path(data_path, resource_file_path):
            app.logger.debug(data_path)
            app.logger.debug(resource_file_path)
            return data_path == os.path.commonprefix((data_path,
                resource_file_path))

        if not resource_within_data_path(app.config['DATA_PATH'], abs_path):
            abort(404)

        if not os.path.isfile(abs_path):
            abort(404)

        if uri != modified_uri:
            redirect(uri_path)

        mimetype = guess_type(abs_path)
        if not (mimetype):
            abort(404)

        return send_file(abs_path, mimetype=mimetype[0])

app.add_url_rule('/<path:uri>.<ext>', view_func=ResourceView.as_view('resource'))
