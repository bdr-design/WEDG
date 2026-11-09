"""Builds the bare body once (photo frame) and saves it, so fascia tests start in seconds."""
import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
bpy.ops.wm.read_factory_settings(use_empty=True)
import body
paint = bpy.data.materials.new('paint'); paint.use_nodes = True; b = paint.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.006, 0.006, 0.007, 1); b.inputs['Roughness'].default_value = 0.45
b.inputs['Specular IOR Level'].default_value = 0.15; b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.03
shell = body.build(); shell.data.materials.append(paint)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'out', 'body.blend'))
print('saved', shell.name, len(shell.data.polygons))
