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

#Operators.reset(delete_strokes=False)

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
upred = AndUP1D(QuantitativeInvisibilityUP1D(0), ContourUP1D())
Operators.select(upred)

# chain
bpred = SameShapeIdBP1D()
Operators.bidirectional_chain(ChainPredicateIterator(upred, bpred), NotUP1D(QuantitativeInvisibilityUP1D(0)))

class ShapeZ(BinaryPredicate1D):
    """Sort ViewShapes by their z-index"""
    def __init__(self, scene):
        BinaryPredicate1D.__init__(self)
        self.z_map = dict()
        self.scene = scene

    def __call__(self, i1, i2):
        return self.get_z_curve(i1) < self.get_z_curve(i2)

    def get_z_curve(self, curve, func=GetShapeF1D()):
        shape = func(curve)[0]
        # get the shapes z-index
        z = self.z_map.get(shape.id.first)
        if z is None:
            o = bpy.data.objects[shape.name]
            z = world_to_camera_view(self.scene, self.scene.camera, o.location).z
            self.z_map[shape.id.first] = z
        return z
Operators.sort(ShapeZ(scene))

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
                Interface0DIterator(stroke))
            *color, alpha = material.diffuse
            shape_map[shape] = ([stroke], color, alpha)
        else:
            item[0].append(stroke)
        for v in stroke:
            v.attribute.visible = False

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
        bFirst=True
    path_string +="U\n"
    return path_string


# layer for fills

group_string = "u\n"

if len(shape_map) == 1:
    group_string += write_fill(next(iter(shape_map.values())))
else:
    for k, item in sorted(shape_map.items(), reverse=True):
        group_string += write_fill(item)

group_string += "U\n"

f.write(_LAYERHEADER.format(time.time()))
f.write(group_string)
f.write(_LAYERFOOTER)
f.write(_FOOTER)
f.close()