#  License  : MIT
#  Author   : Jarno Leppänen, Francesco Fantoni
#  Date     : 2014-03-26

import os
import re
import bpy
import time
from freestyle import *
from freestyle.functions import *
from freestyle.predicates import *
from freestyle.types import *
from freestyle.shaders import *
from parameter_editor import *
from freestyle.chainingiterators import *

#Operators.reset(delete_strokes=False)
def join_unary_predicates(upred_list, bpred):
    if not upred_list:
        return TrueUP1D()
    upred = upred_list[0]
    for p in upred_list[1:]:
        upred = bpred(upred, p)
    return upred

# change this values to change visible lines style, default is black lines with 2px thickness    
color = "0.620000 0.580000 0.435000 0.996000 K"    
width = 1.6
    
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
    pyNatureUP1D(Nature.SILHOUETTE),
    pyNatureUP1D(Nature.CREASE),
    ContourUP1D()
]
upred = join_unary_predicates(preds, OrUP1D)
upred = AndUP1D(QuantitativeInvisibilityUP1D(0), upred)
Operators.select(upred)

# chain
Operators.bidirectional_chain(ChainSilhouetteIterator())

# sort
Operators.sort(pyZBP1D())

class AIPathShader(StrokeShader):
    def shade(self, stroke):
        global group_string
        path_string = 'u\n{0}\n[] 0 d\n{1:.6f} w\n0 j\n0 J\n'.format(color, width)
        bFirst = True
        for v in stroke:
            x, y = v.point
            path_string += '{0:.3f} {1:.3f} '.format(x, y)
            if bFirst:
              bFirst=False
              path_string += 'm\n'
            else:
              path_string += 'L\n'
        path_string += 'S\nU\n'
        group_string += path_string

shaders_list = [
    SamplingShader(50),
    AIPathShader(),
    ConstantColorShader(0, 0, 1),
    ConstantThicknessShader(10)
    ]
    
group_string = "u\n"
Operators.create(TrueUP1D(), shaders_list)
group_string += "U\n"

f.write(_LAYERHEADER.format(time.time()))
f.write(group_string)
f.write(_LAYERFOOTER)
f.write(_FOOTER)
f.close()