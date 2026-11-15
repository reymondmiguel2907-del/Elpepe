"""Six empty domino tables, four inward-facing seats each; reusable geometry."""
import bpy
import json
import math
import os
from mathutils import Vector

FLOOR_Z = .08
CHAIR_OFFSET = .95
TABLE_CENTERS = [(x, y) for y in (2.5, 6.1) for x in (-4.0, 0.0, 4.0)]


def _chair_template(material):
    parts = []

    def part(name, location, size, bevel=.018):
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.dimensions = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(material)
        modifier = obj.modifiers.new('Bordes de silla', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        parts.append(obj)

    part('Asiento plastico', (0, 0, .47), (.46, .44, .065))
    for x in (-.17, .17):
        for y in (-.16, .16):
            part('Pata de silla', (x, y, .245), (.045, .045, .45))
    part('Respaldo de silla', (0, .19, .78), (.46, .045, .53))
    for x in (-.24, .24):
        part('Brazo de silla', (x, 0, .68), (.045, .44, .055))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = 'Plantilla de silla vacia'
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return obj


def create_seating(out_dir, chair_material, collision_box):
    source = os.path.join(out_dir, 'assets', 'mesa-el-bloke-sin-fichas.blend')
    wanted = ['Mesa negra con cuatro portavasos y cuatro ranuras',
              'Cuadro central — logo EL BLOKE']
    with bpy.data.libraries.load(source, link=False) as (available, loaded):
        loaded.objects = [name for name in available.objects if name in wanted]
    table_templates = [obj for obj in loaded.objects if obj is not None]
    assert len(table_templates) == 2, 'Falta la mesa o su logo original'
    chair_template = _chair_template(chair_material)
    layout = {
        'version': 2,
        'coordinate_system': 'threejs_y_up',
        'character_forward_convention': 'negative_z',
        'table_count': 6,
        'chair_count': 24,
        'characters_included': False,
        'domino_tiles_included': False,
        'tables': [],
    }
    # The chair back faces local +Y, so the occupant looks along local -Y.
    seat_offsets = [
        ('sur', 0, -CHAIR_OFFSET, math.pi),
        ('norte', 0, CHAIR_OFFSET, 0),
        ('oeste', -CHAIR_OFFSET, 0, math.pi / 2),
        ('este', CHAIR_OFFSET, 0, -math.pi / 2),
    ]
    for index, (x, y) in enumerate(TABLE_CENTERS, 1):
        table_id = 'mesa-%02d' % index
        entry = {'id': table_id, 'position': [x, FLOOR_Z, -y], 'seats': []}
        for template in table_templates:
            obj = template.copy()
            obj.data = template.data
            bpy.context.collection.objects.link(obj)
            obj.name = '%s / %s' % (table_id, 'logo EL BLOKE' if 'logo' in template.name else 'mesa domino')
            obj.location = template.location + Vector((x, y, FLOOR_Z))
            obj['table_id'] = table_id
            obj['preserve_instance'] = True
        collision_box(table_id, (x, y, FLOOR_Z + .50), (1.0, 1.0, 1.0))
        for side, dx, dy, angle in seat_offsets:
            sx, sy = x + dx, y + dy
            seat_id = table_id + '-asiento-' + side
            chair = chair_template.copy()
            chair.data = chair_template.data
            bpy.context.collection.objects.link(chair)
            chair.name = seat_id + ' / silla vacia'
            chair.location = (sx, sy, FLOOR_Z)
            chair.rotation_euler[2] = angle
            chair['seat_id'] = seat_id
            chair['table_id'] = table_id
            chair['preserve_instance'] = True
            collision_box(seat_id, (sx, sy, FLOOR_Z + .52), (.55, .55, 1.1))
            facing = Vector((x - sx, 0, -(y - sy))).normalized()
            yaw = math.atan2(-facing.x, -facing.z)
            # Empty attachment marker, not a visible character or avatar.
            anchor = bpy.data.objects.new(seat_id + ' / punto de asiento', None)
            bpy.context.collection.objects.link(anchor)
            anchor.location = (sx, sy, FLOOR_Z + .5025)
            anchor.rotation_euler[2] = angle
            anchor.empty_display_type = 'ARROWS'
            anchor.empty_display_size = .10
            anchor['seat_id'] = seat_id
            anchor['table_id'] = table_id
            anchor['occupied'] = False
            entry['seats'].append({
                'id': seat_id,
                'side': side,
                'seat_surface_position': [sx, FLOOR_Z + .5025, -sy],
                'floor_position': [sx, FLOOR_Z, -sy],
                'facing_direction': list(facing),
                'yaw_y_radians': yaw,
                'occupied': False,
            })
        layout['tables'].append(entry)
    bpy.data.objects.remove(chair_template, do_unlink=True)
    for obj in table_templates:
        bpy.data.objects.remove(obj, do_unlink=True)
    with open(os.path.join(out_dir, 'seating-layout.json'), 'w') as handle:
        json.dump(layout, handle, indent=2)
    return layout
