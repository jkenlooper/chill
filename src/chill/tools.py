import os.path
import glob

from pystache.context import ContextStack
import yaml

def build_context_data(app):
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

    app.data = {}
    for (dirpath, dirnames, filenames) in os.walk(app.config['DATA_PATH'], topdown=True):
        filenames.sort() # affects which data fragments get replaced by yaml or other files
        start = len(os.path.commonprefix((app.config['DATA_PATH'], dirpath)))
        relative_path = dirpath[start+1:]
        d = {}
        for f in filenames: #filenames here are considered page fragments
            file_path = os.path.join(dirpath, f)
            (filename, ext) = os.path.splitext(f)
            if filename[:1] == '.':
                continue
            if ext in ('.html', '.htm', '.txt'):
                h = open(file_path, 'r')
                s = h.read()
                if ext == '.txt':
                    s = s.strip()
                d[filename] = s
            if ext in ('.yaml', '.yml'):
                h = open(file_path, 'r')
                y = yaml.load(h)
                if y:
                    d.update(y)


        search_dirs = build_search_dirs(relative_path)

        ctx = ContextStack(d)
        ctx_list = []
        #parent_pages = os.path.dirname(relative_path).split('/')
        parent_page = os.path.dirname(relative_path)
        if parent_page in app.data:
            ctx_list.insert(0, app.data[parent_page])
            #parent_page = os.path.dirname(parent_page)
        ctx_list.append(ctx)
        ctx_with_parent = ContextStack.create(*ctx_list)

        #add the theme dir to search_dirs
        themename = ctx_with_parent.get('_theme', 'default')
        search_dirs.append(os.path.join(app.config['THEME_PATH'], themename))
        ctx_with_parent.push({'_search_dirs':search_dirs})

        app.data[relative_path] = ctx_with_parent

#build_context_data()
#app.build_context_data = build_context_data



