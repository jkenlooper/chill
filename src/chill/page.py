import os.path

from flask import abort, redirect, Blueprint, current_app, render_template
from flask.views import MethodView
from pystache.context import KeyNotFoundError
from pystache.renderer import Renderer

page = Blueprint('page', __name__)

# TODO: decouple the `Page` from any specific template rendering language
# TODO: Create a `PageData` for data that will be rendered with the template
#
class Page(object):
    """
    A page uses a template to render it's data found at the 'uri_path' which is
    passed to it on init.
    """
    # base is the default mustach template and is only used if '_template' is
    # not set for a page
    template = "{{> base}}"
    context = None
    def __init__(self, uri_path):
        self.uri_path = uri_path
        self.context = current_app.data[uri_path]

    def render(self, **kwargs):
        """
        render the page
        """

        try:
            template_name = '%s.mustache' % current_app.data[self.uri_path].get('_template')
        except KeyNotFoundError:
            # something that shouldn't exist
            template_name = '.mustache'

        try:
            search_dirs=current_app.data[self.uri_path].get('_search_dirs')
        except KeyNotFoundError:
            search_dirs = u''

        for d in search_dirs:
            template_path = os.path.join(d, template_name)
            if os.path.exists(template_path):
                template_file = open(template_path, 'r')
                self.template = template_file.read()
                template_file.close()
                break


        renderer = Renderer(search_dirs=search_dirs)
        return renderer.render(self.template, self.context, **kwargs)

# TODO: Change how the 404 stuff is handled.

class PageView(MethodView):
    """
    Handles access to a page.
    """

    def get(self, uri=''):
        """
        view a page
        """
        # check if page exists in data_path

        # a//b == a/b/ == a/./b == a/foo/../b
        uri = os.path.normpath(uri)

        uri, ext = os.path.splitext(uri)

        uri_split = uri.split('/')
        uri_path = os.path.join(*uri_split)
        abs_path = os.path.join(current_app.config['DATA_PATH'], uri_path)
        if not os.path.isdir(abs_path):
            abort(404)

        if (os.path.normpath(os.path.join(abs_path, uri_path)) ==
                os.path.normpath(abs_path)):
            # if the uri is the same as DATA_PATH
            uri_path = '' # key for the 'root' Data
        #page = Page(uri_path)

        #return page.render()
        return 


page.add_url_rule('/', view_func=PageView.as_view('page'))
page.add_url_rule('/index.html', view_func=PageView.as_view('index_page'))

# flask auto redirects urls without a '/' on the end to this
page.add_url_rule('/<path:uri>/', view_func=PageView.as_view('page'))
page.add_url_rule('/<path:uri>/index.html', view_func=PageView.as_view('index_page'))
