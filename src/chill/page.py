import os.path

from flask import abort
from flask.views import MethodView
from pystache.renderer import Renderer
from pystache.context import Context

from chill import app

class Page(object):
    """
    """
    template = "{{> base}}"
    context = None
    def __init__(self, uri_path):
        # set the context
        # set the template
        self.uri_path = uri_path
        self.context = app.data[uri_path]
        pass

    def render(self, **kwargs):
        """
        render the page
        """

        template_name = '%s.mustache' % app.data[self.uri_path].get('_template')
        search_dirs=app.data[self.uri_path].get('_search_dirs')
        for d in search_dirs:
            template_path = os.path.join(d, template_name)
            if os.path.exists(template_path):
                template_file = open(template_path, 'r')
                self.template = template_file.read()
                template_file.close()
                break


        renderer = Renderer(search_dirs=search_dirs)
        return renderer.render(self.template, self.context, **kwargs)

class PageView(MethodView):
    """
    """

    def get(self, uri='index'):
        """
        view a page
        """
        # check if page exists in data_path

        # a//b == a/b/ == a/./b == a/foo/../b
        uri = os.path.normpath(uri)

        uri, ext = os.path.splitext(uri)

        uri_split = uri.split('/')
        uri_path = os.path.join(*uri_split)
        abs_path = os.path.join(app.config['DATA_PATH'], uri_path)
        if not os.path.isdir(abs_path):
            abort(404)

        page = Page(uri_path)

        return page.render()

app.add_url_rule('/', view_func=PageView.as_view('page'))
app.add_url_rule('/<path:uri>', view_func=PageView.as_view('page'))
