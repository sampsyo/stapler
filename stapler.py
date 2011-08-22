from collections import namedtuple
import sys
import os
import jinja2
import jinja2.sandbox

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

class Site(object):
    def __init__(self, fn):
        with open(fn) as f:
            self.routes = _parse_config(f)
        self.basedir = os.path.dirname(os.path.abspath(fn))
        self.outdir = os.path.join(self.basedir, '_out')

        self.env = jinja2.sandbox.SandboxedEnvironment(
            loader=jinja2.FileSystemLoader(self.basedir)
        )

    def render(self):
        if not os.path.isdir(self.outdir):
            os.mkdir(self.outdir)

        for route in self.routes:
            tmpl = self.env.get_template(route.template)
            path = route.path
            if path.endswith('/'):
                path += 'index.html'
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
