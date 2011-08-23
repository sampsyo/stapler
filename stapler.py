from collections import namedtuple
import sys
import os
import jinja2
import jinja2.sandbox
import re
import yaml

INDEX_FILENAME = 'index.html'
BUILD_DIR = '_out'
CONTENT_DIR = 'items'
STATIC_DIR = 'media'
TEMPLATES_DIR = 'templates'
SEPORATOR_RE = re.compile(r'\s*^---\n', re.MULTILINE)

Route = namedtuple('Route', ['path', 'template', 'block'])

def _parse_config(f):
    routes = []
    cur_route = None

    for line in f:
        if line.startswith('/'):
            # Route declaration.
            line = line.strip()
            path, tmpl = line.split(None, 1)
            cur_route = Route(path, tmpl, [])
            routes.append(cur_route)

        elif line.startswith(' ') or line.startswith('\t'):
            # Line in route block.
            if not cur_route:
                raise ValueError()
            else:
                cur_route.block.append(line.lstrip())

    return routes

class Item(object):
    def __init__(self, attrs, body):
        self.attrs = attrs
        self.body = body

    def __str__(self):
        return str(self.body)

    def __unicode__(self):
        return unicode(self.body)

    @classmethod
    def from_string(cls, s):
        m = SEPORATOR_RE.match(s)
        if not m:
            # No attributes.
            attrs = ''
            body = s
        else:
            rest = s[m.end():]
            m = SEPORATOR_RE.search(rest)
            if not m:
                # No body.
                attrs = rest
                body = ''
            else:
                attrs = rest[:m.start()]
                body = rest[m.end():]
        return cls(yaml.load(attrs) or {}, body)

class FSSource(object):
    def __init__(self, path):
        self.path = path

    def _items(self):
        for dirpath, dirnames, filenames in os.walk(self.path,
                                                    followlinks=True):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                filepath = os.path.join(dirpath, filename)
                with open(filepath) as f:
                    content = f.read()
                yield Item.from_string(content)

    def __iter__(self):
        return self._items()

class Site(object):
    def __init__(self, fn):
        with open(fn) as f:
            self.routes = _parse_config(f)

        self.basedir = os.path.dirname(os.path.abspath(fn))
        tmpldir = os.path.join(self.basedir, TEMPLATES_DIR)
        self.outdir = os.path.join(self.basedir, BUILD_DIR)
        contentdir = os.path.join(self.basedir, CONTENT_DIR)
        self.staticdir = os.path.join(self.basedir, STATIC_DIR)

        self.env = jinja2.sandbox.SandboxedEnvironment(
            loader=jinja2.FileSystemLoader(tmpldir)
        )
        self.source = FSSource(contentdir)

    def render(self):
        if not os.path.isdir(self.outdir):
            os.mkdir(self.outdir)

        for route in self.routes:
            tmpl = self.env.get_template(route.template)
            path = route.path
            if path.endswith('/'):
                path += INDEX_FILENAME
            if path.startswith('/'):
                path = path[1:]
            outfn = os.path.join(self.outdir, path)
            print self.outdir, path, outfn

            with open(outfn, 'w') as f:
                for block in tmpl.generate():
                    f.write(block)

if __name__ == '__main__':
    site = Site(sys.argv[1])
    site.render()
