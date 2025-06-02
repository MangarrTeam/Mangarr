from django import template

register = template.Library()

class CaptureAsNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output.strip()
        return ''

@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        tag_name, varname = token.contents.split()
    except ValueError:
        raise template.TemplateSyntaxError("Usage: {% captureas varname %}...{% endcaptureas %}")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureAsNode(nodelist, varname)
