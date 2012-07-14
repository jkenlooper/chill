#chill - Simple Frozen website management
#Copyright (C) 2012  Jake Hickenlooper
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import glob

from pystache.context import ContextStack
import yaml

def build_context_data(app):
    """
    Walks the data path and builds the context data from all files found that
    have the extension of '.html, .htm, .txt, .yaml, .yml'.  HTML and text
    files use the filename without ext as their data name.  YAML files are
    loaded and update the data.
    """
    def build_search_dirs(relative_path):
        """ checks each dir for .mustache templates """
        parent_path = relative_path
        search_dirs = []
        while parent_path != '':
            path = os.path.join(app.config['DATA_PATH'], parent_path)
            if glob.glob(os.path.join(path, "*.mustache")):
                search_dirs.append(path)
            parent_path = os.path.dirname(parent_path)
        return search_dirs

    # TODO: There may be a better way of attaching the data to the app instead
    # of just doing this.
    app.data = {}

    for (dirpath, dirnames, filenames) in os.walk(app.config['DATA_PATH'], topdown=True):
        filenames.sort() # affects which data fragments get replaced by yaml or other files
        start = len(os.path.commonprefix((app.config['DATA_PATH'], dirpath)))
        relative_path = dirpath[start+1:]
        d = {}
        for f in filenames:
            file_path = os.path.join(dirpath, f)
            (filename, ext) = os.path.splitext(f)
            if filename[:1] == '.':
                continue
            if ext in ('.html', '.htm', '.txt'):
                #filenames here are considered page fragments
                h = open(file_path, 'r')
                s = h.read()
                if ext == '.txt':
                    s = s.strip()
                d[filename] = s
            if ext in ('.yaml', '.yml'):
                #each top level key is used as a page fragment
                h = open(file_path, 'r')
                y = yaml.load(h)
                if y:
                    d.update(y)


        search_dirs = build_search_dirs(relative_path)

        ctx = ContextStack(d)
        ctx_list = []
        parent_page = os.path.dirname(relative_path)
        if parent_page in app.data:
            ctx_list.insert(0, app.data[parent_page])
        ctx_list.append(ctx)
        ctx_with_parent = ContextStack.create(*ctx_list)

        #add the theme dir to search_dirs
        themename = ctx_with_parent.get('_theme', 'default')
        search_dirs.append(os.path.join(app.config['THEME_PATH'], themename))
        ctx_with_parent.push({'_search_dirs':search_dirs})

        app.data[relative_path] = ctx_with_parent
