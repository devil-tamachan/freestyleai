#  License  : MIT
#  Author   : Francesco Fantoni
#  Date     : 2014-03-28

import os
import re
import bpy

from parameter_editor import *

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et
    
# set here your frames-per-second rate
fps = 10

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


# shade and write svg

tree = et.parse(path)
root = tree.getroot()


# layer for the frame
if tree.find(".//{http://www.w3.org/2000/svg}g[@id='frame_%06d']" % current_frame) is None:
	layer_frame = et.XML('<g id="frame_%06d"></g>' % current_frame)
	layer_frame.set('{http://www.inkscape.org/namespaces/inkscape}groupmode', 'layer')
	layer_frame.set('{http://www.inkscape.org/namespaces/inkscape}label', 'frame_%06d' % current_frame)
	root.append(layer_frame)
else:
	layer_frame = tree.find(".//{http://www.w3.org/2000/svg}g[@id='frame_%06d']" % current_frame)

# SVG animation stuff
frames = tree.findall("*")
n_of_frames = len(frames)
keyTimes = ""
for n in range(0, n_of_frames):
	keyTimes += "%.3f" % (n/n_of_frames) + ";"
keyTimes += "1"
dur = (n_of_frames / fps)

animation_tags = tree.findall(".//{http://www.w3.org/2000/svg}animate")

for n in range(0, len(animation_tags)):
	values = ""
	for m in range(0, len(animation_tags)):
		if m == n:
			values+="inline;"
		else:
			values+="none;"
	animation_tags[n].set('values', values+"none;none")
	
values = ""
for n in range(1, n_of_frames):
	values += "none;"
values += "inline;none"

if tree.find(".//{http://www.w3.org/2000/svg}animate[@id='anim_%06d']" % current_frame) is None:
	frame_anim = et.XML('<animate id="anim_%06d" />' % current_frame)
	frame_anim.set('attributeName', 'display')
	frame_anim.set('values', values)
	frame_anim.set('repeatCount', 'indefinite')
	frame_anim.set('begin', '0s')
	frame_anim.set('keyTimes', keyTimes)
	frame_anim.set('dur', str(dur)+"s")
	layer_frame.append(frame_anim)
	
for e in tree.findall(".//{http://www.w3.org/2000/svg}animate"):
	e.set('keyTimes', keyTimes)
	e.set('dur', str(dur)+"s")


# prettifies XML
def indent(elem, level=0):
	i = "\n" + level*"  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

indent(root)

# write SVG to file
tree.write(path, encoding='UTF-8', xml_declaration=True)
