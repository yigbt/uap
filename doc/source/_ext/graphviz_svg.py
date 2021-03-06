# -*- coding: utf-8 -*-
"""
    sphinx.ext.graphviz
    ~~~~~~~~~~~~~~~~~~~

    Allow graphviz-formatted graphs to be included in Sphinx-generated
    documents inline.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import posixpath
from os import path
from subprocess import Popen, PIPE
try:
    from hashlib import sha256 as sha
except ImportError:
    from sha import sha

from docutils import nodes

from sphinx.errors import SphinxError
from sphinx.util import ensuredir
from sphinx.util.compat import Directive


mapname_re = re.compile(r'<map id="(.*?)"')


class GraphvizError(SphinxError):
    category = 'Graphviz error'


class graphviz(nodes.General, nodes.Element):
    pass


class Graphviz(Directive):
    """
    Directive to insert arbitrary dot markup.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        dotcode = '\n'.join(self.content)
        if not dotcode.strip():
            return [self.state_machine.reporter.warning(
                'Ignoring "graphviz" directive without content.',
                line=self.lineno)]
        node = graphviz()
        node['code'] = dotcode
        node['options'] = []
        return [node]


class GraphvizSimple(Directive):
    """
    Directive to insert arbitrary dot markup.
    """
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        node = graphviz()
        node['code'] = '%s %s {\n%s\n}\n' % \
                       (self.name, self.arguments[0], '\n'.join(self.content))
        node['options'] = []
        return [node]


def render_dot(self, code, options, format, prefix='graphviz'):
    """
    Render graphviz code into a PNG or PDF output file.
    """
    hashkey = code.encode('utf-8') + str(options) + \
        str(self.builder.config.graphviz_dot_args)
    fname = '%s-%s.%s' % (prefix, sha(hashkey).hexdigest(), format)
    if hasattr(self.builder, 'imgpath'):
        # HTML
        relfn = posixpath.join(self.builder.imgpath, fname)
        outfn = path.join(self.builder.outdir, '_images', fname)
    else:
        # LaTeX
        relfn = fname
        outfn = path.join(self.builder.outdir, fname)

    if path.isfile(outfn):
        return relfn, outfn

    if hasattr(self.builder, '_graphviz_warned_dot') or \
       hasattr(self.builder, '_graphviz_warned_ps2pdf'):
        return None, None

    ensuredir(path.dirname(outfn))

    dot_args = [self.builder.config.graphviz_dot]
    dot_args.extend(self.builder.config.graphviz_dot_args)
    dot_args.extend(options)
    dot_args.extend(['-T' + format, '-o' + outfn])
    if format == 'png':
        dot_args.extend(['-Tcmapx', '-o%s.map' % outfn])
    try:
        p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    except OSError as err:
        if err.errno != 2:   # No such file or directory
            raise
        self.builder.warn('dot command %r cannot be run (needed for graphviz '
                          'output), check the graphviz_dot setting' %
                          self.builder.config.graphviz_dot)
        self.builder._graphviz_warned_dot = True
        return None, None
    # graphviz expects UTF-8 by default
    if isinstance(code, str):
        code = code.encode('utf-8')
    stdout, stderr = p.communicate(code)
    if p.returncode != 0:
        raise GraphvizError('dot exited with error:\n[stderr]\n%s\n'
                            '[stdout]\n%s' % (stderr, stdout))
    return relfn, outfn


def render_svg_tag(svgref, svgfile, imgcls=None):
    # Webkit can't figure out svg dimensions when using object tag
    # so we need to get it from the svg file
    regex = r'<svg\swidth="(\d+)pt"\sheight="(\d+)pt"'
    with open(svgfile, 'r') as f:
        svg = f.read()
    dimensions = re.search(regex, svg, re.M).groups()

    # We need this hack to make WebKit show our object tag properly
    def convert_pt2px(x):
        from math import ceil
        return int(ceil((96.0 / 72.0) * float(x)))

    style = 'width="%s" height="%s"' % tuple(map(convert_pt2px, dimensions))

    # The object tag works fine on Firefox and WebKit
    # Besides it's a hack, this strategy do not mess with templates.
    imgcss = imgcls and 'class="%s"' % imgcls or ''
    html = '<object type="image/svg+xml" data="%s" %s %s/>\n' % \
           (svgref, imgcss, style)
    return html


def render_dot_html(self, node, code, options, prefix='graphviz', imgcls=None):
    format = self.builder.config.graphviz_output_format
    try:
        fname, outfn = render_dot(self, code, options, format, prefix)
    except GraphvizError as exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode

    self.body.append(self.starttag(node, 'p', CLASS='graphviz'))
    if fname is None:
        self.body.append(self.encode(code))
    else:
        if format is 'svg':
            svgtag = render_svg_tag(fname, outfn, imgcls)
            self.body.append(svgtag)
        else:
            mapfile = open(outfn + '.map', 'rb')
            try:
                imgmap = mapfile.readlines()
            finally:
                mapfile.close()
            imgcss = imgcls and 'class="%s"' % imgcls or ''
            if len(imgmap) == 2:
                # nothing in image map (the lines are <map> and </map>)
                self.body.append('<img src="%s" alt="%s" %s/>\n' %
                                 (fname, self.encode(code).strip(), imgcss))
            else:
                # has a map: get the name of the map and connect the parts
                mapname = mapname_re.match(imgmap[0]).group(1)
                self.body.append('<img src="%s" alt="%s" usemap="#%s" %s/>\n' %
                                 (fname, self.encode(code).strip(),
                                  mapname, imgcss))
                self.body.extend(imgmap)

    self.body.append('</p>\n')
    raise nodes.SkipNode


def html_visit_graphviz(self, node):
    render_dot_html(self, node, node['code'], node['options'])


def render_dot_latex(self, node, code, options, prefix='graphviz'):
    try:
        fname, outfn = render_dot(self, code, options, 'pdf', prefix)
    except GraphvizError as exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode

    if fname is not None:
        self.body.append('\\includegraphics{%s}' % fname)
    raise nodes.SkipNode


def latex_visit_graphviz(self, node):
    render_dot_latex(self, node, node['code'], node['options'])


def setup(app):
    app.add_node(graphviz,
                 html=(html_visit_graphviz, None),
                 latex=(latex_visit_graphviz, None))
    app.add_directive('graphviz', Graphviz)
    app.add_directive('graph', GraphvizSimple)
    app.add_directive('digraph', GraphvizSimple)
    app.add_config_value('graphviz_dot', 'dot', 'html')
    app.add_config_value('graphviz_dot_args', [], 'html')
    app.add_config_value('graphviz_output_format', 'png', 'html')
