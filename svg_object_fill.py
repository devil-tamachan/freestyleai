#  License  : MIT
#  Author   : Jarno Leppänen, Francesco Fantoni
#  Date     : 2014-03-26

import os
import re
import bpy
import time
from bpy_extras.object_utils import world_to_camera_view
from freestyle import *
from freestyle.functions import *
from freestyle.predicates import *
from freestyle.types import *
from freestyle.shaders import *
from parameter_editor import *
from freestyle.chainingiterators import *


_HEADER = """\
%!PS-Adobe-3.0 EPSF
"""
_ROOT = """\
%%%%BoundingBox: 0 0 %d %d
"""
_HEADER2 = """\
%AI5_FileFormat 3
%%EndComments
%%BeginProlog
%%EndProlog
%%BeginSetup
%%EndSetup
1 XR
"""

_FOOTER = """\
%%Trailer
%%EOF
"""

_LAYERHEADER = """\
%AI5_BeginLayer
1 1 1 1 0 0 -1 49 80 161 Lb
(New Layer {0:.7f}) Ln
"""
_LAYERFOOTER = """\
LB
%AI5_EndLayer--
"""


scene = getCurrentScene()
current_frame = scene.frame_current
w = scene.render.resolution_x * scene.render.resolution_percentage / 100
h = scene.render.resolution_y * scene.render.resolution_percentage / 100
path = re.sub(r'\.blend$|$', '.ai' , bpy.data.filepath)

# write header if it does not yet exists
try:
  f = open(path, "r+")
  posPrev = 0
  line = f.readline()
  while line != '':
    #print(line)
    if line.rstrip() == "%%Trailer":
      print("found\n")
      f.seek(posPrev)
      f.truncate()
      f.write("\n")
      break
    posPrev = f.tell()
    line = f.readline()
except IOError:
  print("newfile\n")
  f = open(path, "w")
  f.write(_HEADER)
  f.write(_ROOT % (w,h))
  f.write(_HEADER2)

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

def RGB2CMYK(rgb):
  p1 = max(rgb)
  k = 1.0-p1
  c = (1.0-rgb[0]-k)/p1
  m = (1.0-rgb[1]-k)/p1
  y = (1.0-rgb[2]-k)/p1
  return (c, m, y, k)

def write_fill(item):
    cmyk = RGB2CMYK(item[1])
    path_string = 'u\n{0:.6f} {1:.6f} {2:.6f} {3:.6f} k\n'.format(cmyk[0], cmyk[1], cmyk[2], cmyk[3])
    #xml_string = '<path fill-rule="evenodd" fill="#%02x%02x%02x" fill-opacity="%.2f" stroke="none" d="\n' % (tuple(map(lambda c: c * 255, item[1])) + (item[2],))
    bFirst = True
    for stroke in item[0]:
        points = []
        for v in stroke:
            x, y = v.point
            path_string += '{0:.3f} {1:.3f} '.format(x, y)
            if bFirst:
              bFirst=False
              path_string += 'm\n'
            else:
              path_string += 'L\n'
        path_string += 'f\n'
    path_string +="U\n"
    return path_string


# layer for fills

group_string = "u\n"

if len(shape_map) == 1:
    group_string += write_fill(next(iter(shape_map.values())))
else:
    for k, item in sorted(shape_map.items(), key = lambda x: -z_map[x[0]]):
        group_string += write_fill(item)

group_string += "U\n"

f.write(_LAYERHEADER.format(time.time()))
f.write(group_string)
f.write(_LAYERFOOTER)
f.write(_FOOTER)
f.close()