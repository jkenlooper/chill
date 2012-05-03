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
    restricted_dir = None # absolute path of directory to restrict items

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
        abs_path = os.path.join(
                self.restricted_dir(),
                uri_path
                )

        #just in case...
        def resource_within_restricted_path(data_path, resource_file_path):
            return data_path == os.path.commonprefix((data_path,
                resource_file_path))

        if not resource_within_restricted_path(self.restricted_dir(), abs_path):
            abort(404)

        if not os.path.isfile(abs_path):
            abort(404)

        if uri != modified_uri:
            return redirect(uri_path)

        mimetype = guess_type(abs_path)
        if not (mimetype):
            abort(404)

        return send_file(abs_path, mimetype=mimetype[0])

class DataResourceView(ResourceView):
    """
    Allow access to resource files within the data directory.
    """
    
    def restricted_dir(self):
        return app.config['DATA_PATH']

    def get(self, uri, ext=None):
        """
        get the specified resource
        """
        if (ext == 'html') and (uri[len(uri)-5:] == 'index'):
            # Assume that visitor is requesting a page and not just a fragment
            # of a page.
            return redirect('/%s' % uri[:len(uri)-5])
        if ext == None:
            ext = 'html'
        return super(DataResourceView, self).get(uri, ext)

app.add_url_rule('/_data/<path:uri>.html', view_func=DataResourceView.as_view('data_resource'))
app.add_url_rule('/<path:uri>.<ext>', view_func=DataResourceView.as_view('data_resource'))


class ThemesResourceView(ResourceView):
    """
    Allow access to resource files within the themes directory.
    """
    def restricted_dir(self):
        return app.config['THEME_PATH']

app.add_url_rule('/_themes/<path:uri>.<ext>',
        view_func=ThemesResourceView.as_view('themes_resource'))

