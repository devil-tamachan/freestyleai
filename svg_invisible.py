#  License  : MIT
#  Author   : Jarno Leppänen, Francesco Fantoni
#  Date     : 2014-03-26

import os
import re
from freestyle import *
from freestyle.functions import *
from freestyle.predicates import *
from freestyle.types import *
from freestyle.shaders import *
from parameter_editor import *
from freestyle.chainingiterators import *

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

_HEADER = """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n
"""
_ROOT = '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="%d" height="%d"></svg>\n'


SVG_NS = "http://www.w3.org/2000/svg"
et.register_namespace("", SVG_NS)
et.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
et.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")

scene = getCurrentScene()
current_frame = scene.frame_current
w = scene.render.resolution_x * scene.render.resolution_percentage / 100
h = scene.render.resolution_y * scene.render.resolution_percentage / 100
path = re.sub(r'\.blend$|$', '.svg' , bpy.data.filepath)

# write header if it does not yet exists
try:
	with open(path) as f:
		pass
except IOError:
	f = open(path, "w")
	f.write(_HEADER)
	f.write(_ROOT % (w,h))
	f.close()

# select
preds = [
    pyNatureUP1D(Nature.SILHOUETTE),
    pyNatureUP1D(Nature.CREASE),
    ContourUP1D()
]
upred = join_unary_predicates(preds, OrUP1D)
upred = AndUP1D(NotUP1D(QuantitativeInvisibilityUP1D(0)), upred)
Operators.select(upred)

# chain
Operators.bidirectional_chain(ChainSilhouetteIterator())

# sort
Operators.sort(pyZBP1D())



# shade and write svg

tree = et.parse(path)
root = tree.getroot()


class SVGPathShader(StrokeShader):
    def shade(self, stroke):
        xml_string = '<path fill="none" stroke="black" stroke-width="1" stroke-dasharray="2,2" d="\nM '
        for v in stroke:
            x, y = v.point
            xml_string += '%.3f,%.3f ' % (x, h - y)
        xml_string += '" />'
        invisible_element = et.XML(xml_string)
        group_invisible.append(invisible_element)

shaders_list = [
    SamplingShader(50),
    SVGPathShader(),
    ConstantColorShader(1, 0, 0),
    ConstantThicknessShader(10)
    ]

# layer for the frame
if tree.find(".//{http://www.w3.org/2000/svg}g[@id='frame_%06d']" % current_frame) is None:
	layer_frame = et.XML('<g id="frame_%06d"></g>' % current_frame)
	layer_frame.set('{http://www.inkscape.org/namespaces/inkscape}groupmode', 'layer')
	layer_frame.set('{http://www.inkscape.org/namespaces/inkscape}label', 'frame_%06d' % current_frame)
	root.append(layer_frame)
else:
	layer_frame = tree.find(".//{http://www.w3.org/2000/svg}g[@id='frame_%06d']" % current_frame)

# layer for invisible lines
layer_invisible = et.XML('<g  id="layer_invisible"></g>')
layer_invisible.set('{http://www.inkscape.org/namespaces/inkscape}groupmode', 'layer')
layer_invisible.set('{http://www.inkscape.org/namespaces/inkscape}label', 'invisible')
layer_frame.append(layer_invisible)
group_invisible = et.XML('<g id="invisible"></g>' )
layer_invisible.append(group_invisible)
    

Operators.create(TrueUP1D(), shaders_list)

tree.write(path, encoding='UTF-8', xml_declaration=True)
