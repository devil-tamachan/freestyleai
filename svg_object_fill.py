#  License  : MIT
#  Author   : Jarno Leppänen, Francesco Fantoni
#  Date     : 2014-03-26

import os
import re
import bpy
from bpy_extras.object_utils import world_to_camera_view
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
    ContourUP1D(),
    NotUP1D(pyIsOccludedByItselfUP1D())
]
upred = join_unary_predicates(preds, AndUP1D)
Operators.select(upred)

# chain
class ViewshapeChainingIterator(ChainingIterator):
    def init(self):
        pass
    def traverse(self, iter):
        global prev_point, last_point
        edge = self.current_edge
        viewshape = self.current_edge.viewshape
        it = AdjacencyIterator(iter)
        while not it.is_end:
            ve = it.object
            if viewshape.id == ve.viewshape.id:
                last_point = ve.last_viewvertex.point_2d
                return ve
            it.increment()
        return None
Operators.bidirectional_chain(ViewshapeChainingIterator())

get_shape_list = GetShapeF1D()
def get_shape(curve):
    return get_shape_list(curve)[0]

z_map = {}
def get_z(shape):
    global z_map
    global scene
    z = z_map.get(shape.id.first)
    if z == None:
        o = bpy.data.objects[shape.name]
        z = world_to_camera_view(scene, scene.camera, o.location)[2]
        z_map[shape.id.first] = z
    return z
def get_curve_z(curve):
    return get_z(get_shape(curve))

# sort
class ShapeZ(BinaryPredicate1D):
    def __call__(self, i1, i2):
        return get_curve_z(i1) < get_curve_z(i2)
Operators.sort(ShapeZ())

# shade and write svg

tree = et.parse(path)
root = tree.getroot()

shape_map = {}

class ViewShapeColorShader(StrokeShader):
    def shade(self, stroke):
        global shape_map
        shape = GetShapeF1D()(stroke)[0]
        shape = shape.id.first
        item = shape_map.get(shape)
        if item == None:
            material = CurveMaterialF0D()(
                Interface0DIterator(stroke.stroke_vertices_begin()))
            color = material.diffuse[0:3]
            alpha = material.diffuse[3]
            item = ([stroke], color, alpha)
            shape_map[shape] = item
        else:
            item[0].append(stroke)
        for v in stroke:
            v.attribute.color = item[1]

shaders_list = [
    SamplingShader(50),
    ViewShapeColorShader(),
    ConstantThicknessShader(5)
    ]
Operators.create(TrueUP1D(), shaders_list)

def write_fill(item):
    xml_string = '<path fill-rule="evenodd" fill="#%02x%02x%02x" fill-opacity="%.2f" stroke="none" d="\n' % (tuple(map(lambda c: c * 255, item[1])) + (item[2],))
    for stroke in item[0]:
        points = []
        xml_string += 'M '
        for v in stroke:
            x, y = v.point
            xml_string += '%.3f,%.3f ' % (x, h - y)
        xml_string += 'z'
    xml_string +='" />'
    return xml_string

# layer for the frame
if tree.find(".//{http://www.w3.org/2000/svg}g[@id='frame_%06d']" % current_frame) is None:
	layer_frame = et.XML('<g id="frame_%06d"></g>' % current_frame)
	layer_frame.set('{http://www.inkscape.org/namespaces/inkscape}groupmode', 'layer')
	layer_frame.set('{http://www.inkscape.org/namespaces/inkscape}label', 'frame_%06d' % current_frame)
	root.append(layer_frame)
else:
	layer_frame = tree.find(".//{http://www.w3.org/2000/svg}g[@id='frame_%06d']" % current_frame)


# layer for fills
layer_fills = et.XML('<g  id="layer_fills"></g>')
layer_fills.set('{http://www.inkscape.org/namespaces/inkscape}groupmode', 'layer')
layer_fills.set('{http://www.inkscape.org/namespaces/inkscape}label', 'fills')
layer_frame.append(layer_fills)
group_fills = et.XML('<g id="fills"></g>' )
layer_fills.append(group_fills)

if len(shape_map) == 1:
    fill = et.XML(write_fill(next(iter(shape_map.values()))))
    group_fills.append(fill)
else:
    for k, item in sorted(shape_map.items(), key = lambda x: -z_map[x[0]]):
        fill = et.XML(write_fill(item))
        group_fills.append(fill)

tree.write(path, encoding='UTF-8', xml_declaration=True)
