#  License  : MIT
#  Author   : Jarno Leppänen, Francesco Fantoni
#  Date     : 2014-03-24

import re
import bpy
import freestyle

_HEADER = """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg"
    width="%d" height="%d">
"""

scene = freestyle.utils.getCurrentScene()
current_frame = scene.frame_current
path = re.sub(r'\.blend$|$', '.svg' , bpy.data.filepath)
w = scene.render.resolution_x * scene.render.resolution_percentage / 100
h = scene.render.resolution_y * scene.render.resolution_percentage / 100

try:
    f_string = open(path).read()
    if not _HEADER % (w,h) in f_string:
        print ("culo1")
        f = open(path, "w")
        f.write(_HEADER % (w, h))
        f.close()
		
except:
    print ("culo2")
    f = open(path, "w")
    f.write(_HEADER % (w, h))
    f.close()
