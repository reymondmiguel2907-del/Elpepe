import bpy,math,os,json,sys
from mathutils import Vector,Matrix,Quaternion
OUT=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,OUT)
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'assets','casual_male_import.blend'))
scene=bpy.context.scene;scene.render.fps=30;scene.frame_start=1;scene.frame_end=240
rig=bpy.data.objects['Rig'];human=bpy.data.objects['casual_male']

# Las pistas FBX pueden animar el objeto Rig. Un padre independiente conserva
# la orientacion y posicion de la silla sin alterar esas pistas originales.
root=bpy.data.objects.new('ActorRoot',None);bpy.context.collection.objects.link(root)
root.location=(0,-.60,.01);root.rotation_euler[2]=math.pi
rig.parent=root;rig.matrix_parent_inverse=Matrix.Identity(4)

# Restaurar las texturas originales, que el FBX no enlaza correctamente.
m=bpy.data.materials['Casual_Male'];m.use_nodes=True
n=m.node_tree.nodes;n.clear();p=n.new('ShaderNodeBsdfPrincipled');out=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
p.inputs['Roughness'].default_value=.68;p.inputs['Metallic'].default_value=0
for filename,normal in [('casual_man_color.png',False),('casual_man_normal.png',True)]:
    img=bpy.data.images.load(os.path.join(OUT,'assets',filename),check_existing=True);img.pack()
    t=n.new('ShaderNodeTexImage');t.image=img
    if normal:
        img.colorspace_settings.name='Non-Color';nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.4
        m.node_tree.links.new(t.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])
    else:m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])

# Cache de la animacion original de sentarse y del idle sentado.
base=[]
for f in range(1,241):
    if f<=60:
        action=bpy.data.actions['Rig|Rig|man_sit_start'];src=1+(f-1)*38/59
    else:
        action=bpy.data.actions['Rig|Rig|man_sit_idle'];src=1+(f-60)%121
    rig.animation_data.action=action
    scene.frame_set(int(src),subframe=src-int(src));bpy.context.view_layer.update()
    base.append((rig.matrix_basis.copy(),{b.name:b.matrix_basis.copy() for b in rig.pose.bones}))
rig.animation_data.action=None

def material(name,c,rough=.6,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
white=material('Silla plastica blanca',(.72,.75,.71));black=material('Puntos de ficha de prueba',(.003,.003,.003),.95);ivory=material('Ficha de prueba marfil',(.84,.79,.66),.45)
groundmat=material('Suelo de prueba',(.20,.23,.24),.9)

def box(name,loc,size,mat,bevel=.006):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    if bevel:
        b=o.modifiers.new('Bordes','BEVEL');b.width=bevel;b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
    return o

# Mesa aprobada: no importar fichas anteriores.
with bpy.data.libraries.load(os.path.join(OUT,'..','mesa','mesa-el-bloke-sin-fichas.blend'),link=False) as (a,b):
    b.objects=[name for name in a.objects if name in ['Mesa negra con cuatro portavasos y cuatro ranuras','Cuadro central — logo EL BLOKE']]
for o in b.objects:
    if o:bpy.context.collection.objects.link(o)

# Silla alineada con el contacto de la animacion original.
chair_y=-1.03
box('Asiento de silla',(0,chair_y,.463),(.49,.47,.055),white,.025)
box('Respaldo de silla',(0,chair_y-.22,.74),(.48,.055,.52),white,.025)
for x in [-.18,.18]:
    for y in [-.16,.16]:box('Pata de silla',(x,chair_y+y,.235),(.045,.045,.44),white,.01)

# Una sola ficha funcional de prueba; no es el set de fichas definitivo.
parts=[box('Ficha de prueba',(0,0,.005),(.027,.054,.010),ivory,.0017),box('Division',(0,0,.01012),(.023,.0007,.0002),black,.00006)]
for cy,npoints in [(-.0134,[(-1,-1),(1,-1),(-1,1),(1,1)]),(.0134,[(-1,-1),(0,0),(1,1)])]:
    for x,y in npoints:
        bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.0023,depth=.0002,location=(x*.0065,cy+y*.007,.0102));o=bpy.context.object;o.data.materials.append(black);parts.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();prop=bpy.context.object;prop.name='Ficha de prueba 4-3'
scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def ramp(f,a,b):return smooth((f-a)/(b-a))
def world(bone):return rig.matrix_world@rig.pose.bones[bone].matrix
def set_world(name,matrix):rig.pose.bones[name].matrix=rig.matrix_world.inverted()@matrix;bpy.context.view_layer.update()
def rotate_world_bone(name,q):
    current=world(name);loc,rot,sc=current.decompose();set_world(name,Matrix.LocRotScale(loc,q@rot,sc))

analysis=json.load(open(os.path.join(OUT,'hand-rig-analysis.json')))
hand_target=Quaternion((1,0,0),math.radians(-30))@Quaternion(analysis['_palm']['target_hand_world_q'])

# Curvatura controlada de cada falange, ajustable al modelo original.
spec={}
for finger,angles in [('Index',[28,48,18]),('Middle',[32,55,20]),('Ring',[35,58,24]),('Pinky',[38,55,25]),('Thumb',[18,25,18])]:
    for suffix,deg in zip(['','_1','_2'],angles):
        name=finger+suffix+'_R'
        spec[name]=(Vector(analysis[name]['positive_curl_axis_local']),math.radians(deg))

grip_path=os.path.join(OUT,'grip-side-wide-solution.json')
if os.path.exists(grip_path):
    tuned=json.load(open(grip_path))
    if 'grip_rotation_quaternions' in tuned:grip_quats={k:Quaternion(v) for k,v in tuned['grip_rotation_quaternions'].items()}
    else:grip_quats=None
    if 'hand_world_q' in tuned:hand_target=Quaternion(tuned['hand_world_q'])
else:grip_quats=None
free_path=os.path.join(OUT,'free-fingers-pose.json')
if os.path.exists(free_path):
    free=json.load(open(free_path))['best']['quaternions']
    if grip_quats is None:grip_quats={}
    grip_quats.update({k:Quaternion(v) for k,v in free.items()})
# Orientacion final de pinza: nudillos por encima del tablero, sin bajar el
# ultimo segmento del indice a traves de la superficie al recoger o depositar.
hand_target=Quaternion((1,0,0),math.radians(-10))@Quaternion(analysis['_palm']['target_hand_world_q'])

def fingers(amount):
    for name,(axis,angle) in spec.items():
        pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION'
        resting=Quaternion(analysis[name]['basis_q'])
        goal=grip_quats[name] if grip_quats and name in grip_quats else resting@Quaternion(axis,angle)
        pb.rotation_quaternion=resting.slerp(goal,amount)
    bpy.context.view_layer.update()

def apply_base(f):
    matrix,pose=base[f-1];rig.matrix_basis=matrix
    for name,mx in pose.items():rig.pose.bones[name].matrix_basis=mx
    bpy.context.view_layer.update()

# Pinza calculada sobre las puntas reales del indice y el pulgar.
apply_base(100)
h=world('hand_R');set_world('hand_R',Matrix.LocRotScale(h.translation,hand_target,Vector((1,1,1))));fingers(1)
hand_inv=world('hand_R').inverted()
thumb=rig.matrix_world@rig.pose.bones['Thumb_2_R'].tail
index=rig.matrix_world@rig.pose.bones['Index_2_R'].tail
local_grip=hand_inv@((thumb+index)*.5)
# Usar el centro entre yemas para que la ficha viaje exactamente con la mano.
print('GRIP',list(local_grip),'tip_gap',float((thumb-index).length),flush=True)

pickup=Vector((.17,-.35,.7842));placed=Vector((.12,-.23,.7842))
samples=[];checks=[]

def arm_to(target,weight):
    upper=rig.pose.bones['Upper_Arm_R'];lower=rig.pose.bones['Lower_Arm_R']
    sh=world('Upper_Arm_R').translation;original=world('hand_R').translation
    target=original.lerp(target,weight)
    if weight<.00001:return (target-sh).length,0
    length1=(rig.matrix_world@upper.tail-sh).length
    joint=rig.matrix_world@lower.head;length2=(rig.matrix_world@lower.tail-joint).length
    delta=target-sh;dist=delta.length;direction=delta.normalized()
    distance=max(abs(length1-length2)+.001,min(dist,length1+length2-.001))
    target=sh+direction*distance
    elbow_side=Vector((1,0,.1));elbow_side-=direction*elbow_side.dot(direction);elbow_side.normalize()
    initial_side=joint-sh-direction*(joint-sh).dot(direction)
    if initial_side.length>.00001:elbow_side=initial_side.normalized().lerp(elbow_side,weight).normalized()
    along=(length1*length1-length2*length2+distance*distance)/(2*distance)
    elbow=sh+direction*along+elbow_side*math.sqrt(max(0,length1*length1-along*along))
    cur=world('Upper_Arm_R');old=(rig.matrix_world@upper.tail-cur.translation).normalized()
    rotate_world_bone('Upper_Arm_R',old.rotation_difference((elbow-cur.translation).normalized()))
    cur=world('Lower_Arm_R');old=(rig.matrix_world@lower.tail-cur.translation).normalized()
    rotate_world_bone('Lower_Arm_R',old.rotation_difference((target-cur.translation).normalized()))
    return dist,max(0,dist-distance)

for f in range(1,241):
    apply_base(f)
    reach=ramp(f,80,116)*(1-ramp(f,228,240))
    close=ramp(f,114,130)*(1-ramp(f,194,214))
    lean=ramp(f,80,116)*(1-ramp(f,228,240))
    rotate_world_bone('Spine',Quaternion((1,0,0),math.radians(-28)*lean))
    # Traslado suave de la ficha: elevar, llevar, bajar y dejar quieta.
    carry=ramp(f,146,177)
    tilepos=pickup.lerp(placed,carry)
    tilepos.z+=.105*ramp(f,132,146)*(1-ramp(f,178,193))
    if f>=194:tilepos=placed.copy()
    handq=hand_target
    approach_lift=.07*ramp(f,80,112)*(1-ramp(f,114,130))
    release_lift=.08*ramp(f,194,206)
    desired_wrist=tilepos+Vector((0,0,.0175+approach_lift+release_lift))-handq@local_grip
    if f>=214:desired_wrist=desired_wrist.lerp(Vector((.24,-.83,1.0)),ramp(f,214,228))
    dist,clamped=arm_to(desired_wrist,reach)
    h=world('hand_R');loc,oldq,sc=h.decompose()
    set_world('hand_R',Matrix.LocRotScale(loc,oldq.slerp(handq,reach),sc))
    fingers(reach*(.25+.75*close))
    matrices={b.name:b.matrix.copy() for b in rig.pose.bones}
    samples.append((rig.matrix_basis.copy(),matrices,tilepos.copy()))
    if f in [60,116,130,146,177,193,240]:checks.append({'frame':f,'shoulder':list(world('Upper_Arm_R').translation),'wrist':list(world('hand_R').translation),'target':list(desired_wrist),'reach_clamped_m':clamped,'grip_center':list(world('hand_R')@local_grip),'ficha':list(tilepos)})

# Hornear matrices visuales del esqueleto a claves ordinarias, sin IK de motor.
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
action=bpy.data.actions.new('Domino_Sentarse_Agarrar_Colocar');rig.animation_data.action=action;rig.rotation_mode='QUATERNION'
prop.animation_data_create();prop_action=bpy.data.actions.new('Ficha_sincronizada');prop.animation_data.action=prop_action
prop.rotation_mode='QUATERNION'
for f,(object_basis,matrices,tilepos) in enumerate(samples,1):
    scene.frame_set(f);rig.matrix_basis=object_basis
    for b in rig.pose.bones:
        kw={}
        if b.parent:kw={'parent_matrix':matrices[b.parent.name],'parent_matrix_local':b.parent.bone.matrix_local}
        b.matrix_basis=b.bone.convert_local_to_pose(matrices[b.name],b.bone.matrix_local,invert=True,**kw)
        for path in ['location','rotation_quaternion','scale']:b.keyframe_insert(data_path=path,frame=f,group=b.name)
    for path in ['location','rotation_quaternion','scale']:rig.keyframe_insert(data_path=path,frame=f)
    prop.location=tilepos;prop.rotation_quaternion=(1,0,0,0)
    for path in ['location','rotation_quaternion','scale']:prop.keyframe_insert(data_path=path,frame=f)
for a in [action,prop_action]:
    for curve in a.fcurves:
        for key in curve.keyframe_points:key.interpolation='LINEAR'

scene.frame_set(1)
for label,frame in [('Sentarse',1),('Sentado',60),('Alcanzar',80),('Agarrar',130),('Levantar',146),('Colocar',193),('Soltar',201),('Terminar',240)]:scene.timeline_markers.new(label,frame=frame)

# Exportar actor, mesa, silla y una ficha, sin escenario ni luces de estudio.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'personaje-domino-animado.glb'),export_format='GLB',use_selection=True,export_apply=False,export_animations=True,export_animation_mode='SCENE',export_anim_scene_split_object=False,export_frame_range=True,export_force_sampling=True,export_anim_single_armature=True)
with open(os.path.join(OUT,'animation-checks.json'),'w') as f:json.dump({'fps':30,'frames':240,'phases':{'sit':[1,60],'pick':[80,146],'place':[146,209]},'local_grip':list(local_grip),'checks':checks},f,indent=2)
print('EXPORT_READY: personaje-domino-animado.glb',flush=True)

box('Suelo de estudio',(0,-.3,-.02),(200,200,.03),groundmat,.004)
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=False;scene.cycles.max_bounces=4
scene.world.color=(.14,.14,.14);scene.view_settings.view_transform='AgX'
def area(loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.size=size;l.rotation_euler=(Vector((0,-.5,.8))-l.location).to_track_quat('-Z','Y').to_euler()
area((1.5,1.3,3.5),300,3);area((-2,-1,2.7),220,2.5);area((0,-3,2.8),180,2)
bpy.ops.object.camera_add(location=(2.2,1.65,1.85));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.55;cam.rotation_euler=(Vector((0,-.45,.9))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
scene.render.resolution_x=1000;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'personaje-domino-animado.blend'))
if os.environ.get('ANIMATION_SKIP_STILLS')=='1':
    print('DONE: animation exported; still renders skipped',flush=True)
    sys.exit(0)
for name,frame in [('personaje-de-pie',1),('personaje-sentado',70),('personaje-agarrando',148),('personaje-colocando',193)]:
    scene.frame_set(frame);scene.render.filepath=os.path.join(OUT,name+'.png');bpy.ops.render.render(write_still=True)
print('DONE: animacion y cuatro vistas reales',flush=True)
