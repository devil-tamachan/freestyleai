# SVG output for Blender Freestyle

Python style modules for writing SVG output in Blender. Features filled contour paths.

![Table and chair](https://rawgithub.com/hvfrancesco/freestylesvg/master/example/table_and_chair.svg)

*Model by [yellowpanda](http://www.blendswap.com/blends/view/69490)*

## Getting Started

Open the scripts as text blocks in your .blend file and make sure Freestyle python
scripting mode is enabled. Now you can add the scripts as style modules.
You can render still images or animations, the svg file will be written on the same directory of the
source blender file.

When opened in Inkscape each rendered frame will be in a separate layer, with sublayers for the different
types or rendered elements (e.g. fills, invisible lines, visible edges) according to the modules you used
to render.

IMPORTANT: this code uses the new freestyle API introduced in Blender 2.70, it won't work on earlier blender versions

## Animation in SVG

You can automatically output a SVG file that contains frame-by-frame animation using SVG native <animate> tags,
ready to be used on the web, and it will work on most modern browsers. Ain't that cool?
To do this, just add to your freestyle rendering modules the 'animate.py' script, the same way you would do with any other module.
The 'animate' module can go in any position on your module queue, but I suggest to put it in first or last position for a cleaner SVG

![Animated SVG from Blender](https://rawgithub.com/hvfrancesco/freestylesvg/master/example/animated.svg)

## License

MIT
