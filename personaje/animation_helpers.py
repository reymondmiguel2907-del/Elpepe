"""Blender helpers for real humanoid/prop animation and portable glTF baking.

This module does not create a substitute character or assume a particular rig.
The calling script must map the actual arm, wrist and finger bones first.
"""
import bpy
import math
import re
from mathutils import Matrix, Vector, Quaternion


def frame_at(seconds, fps=24, start=1):
    return start + round(seconds * fps)


def new_action(owner, name):
    owner.animation_data_create()
    action = bpy.data.actions.new(name)
    owner.animation_data.action = action
    return action


def key_transform(owner, frame, matrix=None):
    """Key an object's local transform, optionally from a world-space matrix."""
    if matrix is not None:
        owner.matrix_world = matrix
    owner.rotation_mode = 'QUATERNION'
    for path in ('location', 'rotation_quaternion', 'scale'):
        owner.keyframe_insert(data_path=path, frame=frame)


def set_interpolation(action, interpolation='BEZIER', handles='AUTO_CLAMPED'):
    for curve in action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = interpolation
            if interpolation == 'BEZIER':
                key.handle_left_type = handles
                key.handle_right_type = handles


def empty_target(name, location, display_size=.08):
    target = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(target)
    target.empty_display_type = 'SPHERE'
    target.empty_display_size = display_size
    target.location = location
    return target


def key_target(target, keys):
    """keys is an iterable of (frame, world_location). Target must be unparented."""
    if target.parent is not None:
        raise ValueError('Use an unparented IK target for world-space key locations')
    for frame, location in keys:
        target.location = location
        target.keyframe_insert(data_path='location', frame=frame)
    if target.animation_data and target.animation_data.action:
        set_interpolation(target.animation_data.action)


def two_bone_ik(armature, lower_bone, target, pole=None, pole_angle=0,
                name='Domino reach IK'):
    """Reach the forearm/shin TAIL; hand/foot remains separately orientable.

    For arms, lower_bone is the forearm, not the hand. This keeps chain_count=2
    on upper arm + forearm and avoids including the clavicle in the chain.
    """
    bone = armature.pose.bones[lower_bone]
    constraint = bone.constraints.new('IK')
    constraint.name = name
    constraint.target = target
    constraint.chain_count = 2
    constraint.use_tail = True
    constraint.use_stretch = False
    constraint.use_rotation = False
    constraint.iterations = 128
    if pole is not None:
        constraint.pole_target = pole
        constraint.pole_angle = pole_angle
    return constraint


def pole_from_joint(shoulder, elbow, wrist, distance=.35, fallback=(0, -1, 0)):
    """World-space pole that preserves the existing elbow bend direction."""
    shoulder, elbow, wrist = map(Vector, (shoulder, elbow, wrist))
    line = wrist - shoulder
    if line.length_squared < 1e-9:
        return elbow + Vector(fallback).normalized() * distance
    projection = shoulder + line * ((elbow - shoulder).dot(line) / line.length_squared)
    bend = elbow - projection
    if bend.length < 1e-5:
        bend = Vector(fallback)
    return elbow + bend.normalized() * distance


def finger_bones(armature, side='right'):
    """Discover candidates only; does not guess their curl axis or apply a pose."""
    side = side.lower()
    aliases = {'right': ('right', 'r'), 'left': ('left', 'l')}
    long_name, short_name = aliases[side]
    output = []
    for bone in armature.pose.bones:
        name = bone.name.lower()
        digit = any(token in name for token in ('thumb', 'index', 'middle', 'ring', 'pinky', 'little'))
        side_match = (long_name in name or re.search(r'(^|[_.:\-])' + short_name + r'([_.:\-]|$)', name))
        if digit and side_match:
            output.append(bone.name)
    return output


def key_finger_grip(armature, specification, keys):
    """Pose known fingers after inspecting the rig.

    specification maps bone_name -> {'axis': (x,y,z), 'angle': radians,
    'rest': Quaternion (optional)}. Axis is in that pose bone's LOCAL space.
    keys contains (frame, amount), where 0 is open and 1 is the tuned grip.
    Different thumb axes and joint angles must be supplied explicitly.
    """
    resting = {}
    for name, config in specification.items():
        bone = armature.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        resting[name] = Quaternion(config.get('rest', bone.rotation_quaternion.copy()))
    for frame, amount in keys:
        for name, config in specification.items():
            bone = armature.pose.bones[name]
            axis = Vector(config['axis']).normalized()
            bone.rotation_quaternion = resting[name] @ Quaternion(axis, config['angle'] * amount)
            bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)


def sample_pose(armature, frame_start, frame_end):
    """Cache evaluated armature-space matrices before constraints are removed."""
    scene = bpy.context.scene
    old_frame = scene.frame_current
    samples = {}
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        evaluated = armature.evaluated_get(bpy.context.evaluated_depsgraph_get())
        samples[frame] = {bone.name: bone.matrix.copy() for bone in evaluated.pose.bones}
    scene.frame_set(old_frame)
    return samples


def bake_visual_pose(armature, frame_start, frame_end, name, clear_constraints=True):
    """Bake evaluated IK/FK to ordinary bone keys, ready for GLB.

    This intentionally replaces the active action and optionally removes rig
    constraints. Call on a saved copy if the original control rig is needed.
    The source samples are cached before action/constraint changes.
    """
    scene = bpy.context.scene
    samples = sample_pose(armature, frame_start, frame_end)
    if clear_constraints:
        for bone in armature.pose.bones:
            for constraint in list(bone.constraints):
                bone.constraints.remove(constraint)
    action = new_action(armature, name)
    for frame, matrices in samples.items():
        scene.frame_set(frame)
        for bone in armature.pose.bones:
            data_bone = bone.bone
            params = {}
            if bone.parent:
                params['parent_matrix'] = matrices[bone.parent.name]
                params['parent_matrix_local'] = bone.parent.bone.matrix_local
            basis = data_bone.convert_local_to_pose(
                matrices[bone.name], data_bone.matrix_local, invert=True, **params)
            bone.rotation_mode = 'QUATERNION'
            bone.matrix_basis = basis
            for path in ('location', 'rotation_quaternion', 'scale'):
                bone.keyframe_insert(data_path=path, frame=frame)
    set_interpolation(action, 'LINEAR')
    scene.frame_set(frame_start)
    return action


def sample_object_world(owner, frame_start, frame_end):
    scene = bpy.context.scene
    old_frame = scene.frame_current
    samples = {}
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        samples[frame] = owner.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
    scene.frame_set(old_frame)
    return samples


def bake_object_world(owner, frame_start, frame_end, name, clear_constraints=True,
                      detach_parent=True):
    """Bake attachment/Child Of motion into standalone prop transform keys."""
    samples = sample_object_world(owner, frame_start, frame_end)
    if clear_constraints:
        for constraint in list(owner.constraints):
            owner.constraints.remove(constraint)
    if detach_parent:
        owner.parent = None
    action = new_action(owner, name)
    for frame, matrix in samples.items():
        key_transform(owner, frame, matrix)
    set_interpolation(action, 'LINEAR')
    bpy.context.scene.frame_set(frame_start)
    return action


def bake_hand_attachment(prop, armature, hand_bone, pickup_matrix, attach_frame,
                         release_frame, frame_start, frame_end,
                         name='TomarYColocar', release_matrix=None):
    """Bake a prop that follows the real hand only during its grasp interval.

    pickup_matrix is a full WORLD matrix. The grasp offset is calculated from
    the evaluated hand at attach_frame, so attachment has no positional jump.
    If release_matrix is omitted, the prop rests at its final grasped matrix.
    A supplied release_matrix must match the tuned hand path at release_frame;
    a mismatch would be a visible pop and should be fixed in the animation.
    """
    if release_frame < attach_frame:
        raise ValueError('release_frame must not precede attach_frame')
    scene = bpy.context.scene
    hand_matrices = {}
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        evaluated = armature.evaluated_get(bpy.context.evaluated_depsgraph_get())
        hand_matrices[frame] = evaluated.matrix_world @ evaluated.pose.bones[hand_bone].matrix
    offset = hand_matrices[attach_frame].inverted() @ pickup_matrix
    resting = release_matrix or (hand_matrices[release_frame] @ offset)
    prop.parent = None
    for constraint in list(prop.constraints):
        prop.constraints.remove(constraint)
    action = new_action(prop, name)
    for frame in range(frame_start, frame_end + 1):
        if frame < attach_frame:
            matrix = pickup_matrix
        elif frame <= release_frame:
            matrix = hand_matrices[frame] @ offset
        else:
            matrix = resting
        key_transform(prop, frame, matrix)
    set_interpolation(action, 'LINEAR')
    scene.frame_set(frame_start)
    return action, {'grasp_offset': offset, 'release_world': resting}


def add_nla_clip(owner, action, track_name=None, frame_start=1):
    """Use identical track names on armature + prop to group a glTF clip."""
    owner.animation_data_create()
    track = owner.animation_data.nla_tracks.new()
    track.name = track_name or action.name
    strip = track.strips.new(action.name, frame_start, action)
    strip.action_frame_start = action.frame_range[0]
    strip.action_frame_end = action.frame_range[1]
    strip.extrapolation = 'NOTHING'
    strip.blend_type = 'REPLACE'
    return track, strip


SIT_TIMING_SECONDS = {
    'stand': 0.0, 'prepare': .45, 'lower': 1.35, 'contact': 2.1, 'settle': 3.0,
}
PICK_PLACE_TIMING_SECONDS = {
    'seated': 0.0, 'reach': .8, 'touch': 1.1, 'grip': 1.5,
    'lift': 2.05, 'carry': 2.7, 'place': 3.3, 'release': 3.6, 'withdraw': 4.0,
}
