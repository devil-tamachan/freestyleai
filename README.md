# SVG output for Blender Freestyle

Python style modules for writing SVG output in Blender. Features filled contour paths.

![Table and chair](https://rawgithub.com/jlep/freestylesvg/master/example/table_and_chair.svg)

*Model by [yellowpanda](http://www.blendswap.com/blends/view/69490)*

## Getting Started

Open the scripts as text blocks in your .blend file and make sure Freestyle python
scripting mode is enabled. Now you can add the scripts as style modules. `svg_header.py`
should be the first style.
You can render still images or animations, the svg file will be written on the same directory of the
source blender file.
When opened in Inkscape each rendered frame will be in a separate layer, with sublayers for the different
types or rendered elements (e.g. fills, invisible lines, visible edges) according to the modules you used
to render.

## License

MIT
