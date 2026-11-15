"""Render the saved six-table scene without rebuilding or importing characters."""
import bpy
import os
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'colmado-el-bloke.blend'))
scene = bpy.context.scene
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
cam = scene.camera

def capture(name, position, target, lens):
    cam.location = position
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    scene.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)

capture('colmado-interior', (7.8, -.8, 3.55), (0, 5.0, 1.0), 20)
capture('colmado-calle', (10, -12, 3.2), (0, 4, 2), 24)
# The roof remains in the actual model. Cut the presentation camera below it
# only for the overhead seating plan, including older merged-mesh scene files.
cam.data.clip_start = 12.5
capture('distribucion-mesas', (0, 5.0, 16), (0, 5.0, 0), 30)
print('DONE: seating views — six tables, 24 empty chairs', flush=True)
