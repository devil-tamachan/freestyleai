#  License  : MIT
#  Author   : Jarno Leppänen, Francesco Fantoni
#  Date     : 2014-03-24

import re
import bpy
import freestyle
try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

SVG_NS = "http://www.w3.org/2000/svg"

_HEADER = """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n
"""
_ROOT = '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="%d" height="%d"></svg>\n'

scene = freestyle.utils.getCurrentScene()
current_frame = scene.frame_current
path = re.sub(r'\.blend$|$', '.svg' , bpy.data.filepath)
w = scene.render.resolution_x * scene.render.resolution_percentage / 100
h = scene.render.resolution_y * scene.render.resolution_percentage / 100

#et.register_namespace("", SVG_NS)
#et.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")
#et.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")

try:
	with open(path) as f:
		pass
except IOError:
	#root = et.XML(_ROOT % (w,h))
	f = open(path, "w")
	f.write(_HEADER)
	#f.write(et.tostring(root).decode('utf-8'))
	f.write(_ROOT % (w,h))
	f.close()
