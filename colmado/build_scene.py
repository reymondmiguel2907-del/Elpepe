import bpy, math, os, json, random, sys
from mathutils import Vector

OUT=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,OUT)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(31)
COLLIDERS=[]

def mat(name,c,rough=.65,metal=0,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if emission:
        p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emission
    return m

cream=mat('Paredes crema',(.62,.57,.43));red=mat('Zocalo vino',(.30,.035,.035));cement=mat('Cemento',(.30,.32,.31))
ivory=mat('Ceramica clara',(.52,.52,.43),.85);grout=mat('Juntas del suelo',(.24,.25,.22),.9)
asphalt=mat('Asfalto',(.055,.060,.060),.96);stripe=mat('Pintura vial',(.75,.64,.30),.8)
black=mat('Metal negro',(.012,.016,.018),.42,.25);dark=mat('Bocinas negras',(.009,.010,.011),.9)
cone=mat('Conos de bocina',(.022,.026,.026),.9);silver=mat('Metal galvanizado',(.38,.40,.42),.32,.65)
green=mat('Verde El Bloke',(.075,.58,.015),.5);signbg=mat('Fondo cartel',(.012,.035,.020))
white=mat('Blanco rotulos',(.85,.88,.82));wood=mat('Asientos beige',(.40,.28,.15))
glow=mat('Difusor lamparas',(.95,.85,.60),.4,0,2)
glass=mat('Vidrio oscuro de ventanas',(.025,.09,.105),.27,.3)
plants=mat('Hojas verdes',(.035,.16,.035),.85);trunk=mat('Troncos',(.16,.10,.045))
housecolors=[mat('Casa coral',(.52,.21,.15)),mat('Casa azul',(.12,.32,.42)),mat('Casa mostaza',(.57,.39,.13)),mat('Casa verde',(.22,.39,.25)),mat('Casa rosa',(.55,.30,.34)),mat('Casa hueso',(.57,.55,.43))]

def box(name,loc,size,m,bevel=0,collider=False):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    if bevel:
        b=o.modifiers.new('Bordes','BEVEL');b.width=bevel;b.segments=2
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
        b=o.modifiers.new('Normales','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=b.name)
    if collider:o['collider']=True
    return o

def cyl(name,loc,r,d,m,axis=None,n=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=d,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(m)
    if axis=='Y':o.rotation_euler[0]=math.pi/2
    if axis=='X':o.rotation_euler[1]=math.pi/2
    for p in o.data.polygons:
        if len(p.vertices)==4:p.use_smooth=True
    return o

def beam(name,a,b,r,m):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,m,n=10);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def text(name,body,loc,size,m,rot=(math.pi/2,0,0),align='CENTER'):
    bpy.ops.object.text_add(location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.body=body;o.data.align_x=align;o.data.align_y='CENTER';o.data.size=size;o.data.extrude=.004;o.data.materials.append(m)
    bpy.ops.object.convert(target='MESH');return o

def collision_box(name,loc,size):
    x,y,z=loc;sx,sy,sz=size
    COLLIDERS.append({'name':name,'min':[x-sx/2,z-sz/2,-y-sy/2],'max':[x+sx/2,z+sz/2,-y+sy/2]})

# Piso continuo mucho mayor que la zona de paseo: no hay bordes abiertos al alcance.
box('Terreno continuo',(0,0,-.18),(180,180,.24),cement)
box('Calle del barrio',(0,-8.2,-.035),(64,9.2,.10),asphalt)
for x in range(-28,30,6):box('Linea vial',(x,-8.2,.021),(2.5,.11,.006),stripe)
box('Acera frente al colmado',(0,-1.7,.015),(60,3.5,.12),ivory)
box('Acera del barrio',(0,-14.2,.015),(60,2.8,.12),ivory)
box('Bordillo frente',(0,-3.47,.035),(60,.16,.19),cement,.018)
box('Bordillo opuesto',(0,-12.8,.035),(60,.16,.19),cement,.018)

# Colmado 18 x 12 metros: una sola entrada amplia y suelo sin huecos.
box('Suelo colmado',(0,6,.005),(18,12,.15),ivory)
for x in range(-9,10):box('Junta ceramica X',(x,6,.083),(.008,12,.003),grout)
for y in range(13):box('Junta ceramica Y',(0,y,.083),(18,.008,.003),grout)
box('Muro izquierdo',(-9,6,2.2),(.25,12.25,4.4),cream,collider=True)
box('Muro derecho',(9,6,2.2),(.25,12.25,4.4),cream,collider=True)
box('Muro trasero',(0,12,2.2),(18.25,.25,4.4),cream,collider=True)
box('Zocalo izquierdo',(-8.86,6,.45),(.025,12,.9),red)
box('Zocalo derecho',(8.86,6,.45),(.025,12,.9),red)
box('Zocalo trasero',(0,11.86,.45),(18,.025,.9),red)
roof=box('Techo solido',(0,5.1,4.5),(18.7,14.4,.18),cream)
roof['preserve_instance']=True
for x in [-8.8,8.8]:
    box('Columna frontal',(x,-1.6,2.2),(.28,.28,4.4),cream,.02,True)
    box('Columna trasera',(x,10,2.2),(.28,.28,4.4),cream,.02)
for x in [-6,0,6]:box('Viga del techo',(x,5.1,4.33),(.14,14.1,.23),red)
box('Rotulo frontal',(0,-2.13,3.75),(15,.16,.94),signbg,.04)
text('Nombre colmado','COLMADO EL BLOKE',(0,-2.222,3.8),.62,white)
text('Subtitulo colmado','DOMINO  -  MUSICA  -  TU BARRIO',(0,-2.225,3.42),.19,green)

# Iluminacion fisica y difusores modelados.
for x in [-5.5,0,5.5]:
    for y in [2,7,10.5]:
        box('Lampara de techo',(x,y,4.36),(1.2,.32,.06),glow,.02)

# Bocinas dobles con conos, aros y tweeters en volumen real.
for x in [-7.65,7.65]:
    box('Base de bocina',(x,3,.16),(1.05,.85,.32),black,.025,True)
    for z in [.95,2.25]:
        box('Bocina profesional',(x,3,z),(.88,.62,1.22),dark,.045,True)
        for zz in [z-.25,z+.25]:
            cyl('Aro del woofer',(x,2.676,zz),.245,.035,black,'Y',32)
            cyl('Cono del woofer',(x,2.650,zz),.218,.025,cone,'Y',32)
            cyl('Centro del woofer',(x,2.630,zz),.070,.025,black,'Y',20)
        box('Tweeter',(x,2.674,z+.46),(.29,.032,.11),silver,.014)

# Neveras con botellas visibles. Se mantienen opacas para exportar sin problemas.
for xx in [-7.4,-5.8]:
    box('Nevera Presidente',(xx,10.95,1.27),(1.38,1.35,2.42),white,.05,True)
    box('Interior nevera',(xx,10.252,1.35),(1.22,.04,1.88),signbg,.02)
    text('Marca nevera','Presidente',(xx,10.214,2.30),.19,green)
    for z in [.68,1.12,1.56,2.0]:
        box('Rejilla nevera',(xx,10.21,z-.17),(1.18,.06,.023),silver)
        for k in range(6):
            bx=xx+(k-2.5)*.17
            cyl('Botella fria',(bx,10.16,z-.045),.046,.25,green,n=12)
            cyl('Cuello cerveza',(bx,10.16,z+.115),.024,.09,green,n=12)
            box('Etiqueta cerveza',(bx,10.109,z-.02),(.07,.007,.10),white)
    box('Marco puerta nevera',(xx-.66,10.12,1.35),(.04,.05,1.98),silver)
    box('Manija nevera',(xx+.52,10.10,1.35),(.035,.05,.58),silver,.01)

# Cartel de identidad en pared interior.
box('Panel de bienvenida',(-4.7,11.83,3.2),(6.8,.05,.60),signbg,.02)
text('Bienvenida','BIENVENIDOS A EL BLOKE',(-4.7,11.79,3.23),.25,white)
text('Ambiente','DOMINO ENTRE PANAS',(-4.7,11.785,2.99),.14,green)

# Bebidas y mostrador creados en modulo independiente.
from beverage_props import build_beverage_display
build_beverage_display()

# Seis mesas EL BLOKE y 24 sillas vacias; una silla por lado de cada mesa.
from seating_layout import create_seating
seating_layout=create_seating(OUT,white,collision_box)

# Cajas y bolsas de mercancia discretas contra paredes, nunca en el paso central.
crate=mat('Cajas plasticas verdes',(.035,.20,.055),.7)
for x,y in [(-8.2,8),(-8.2,8.7),(8.2,6.5)]:
    for z in [.22,.66]:box('Caja de cerveza',(x,y,z+.08),(.58,.43,.40),crate,.025,True)

# Barrio en ambos lados de la calle: casas con rejas, puertas y techos.
def house(cx,cy,w,d,h,color,front=1):
    box('Casa del barrio',(cx,cy,h/2),(w,d,h),color,.025,True)
    box('Azotea de concreto',(cx,cy,h+.08),(w+.2,d+.2,.16),cement,.02)
    fy=cy+front*(d/2+.025)
    box('Puerta metalica',(cx-.24*w,fy,1.1),(1.15,.08,2.2),black,.02)
    box('Ventana oscura',(cx+.21*w,fy,1.65),(1.55,.09,1.03),glass,.015)
    for dx in [-.68,-.34,0,.34,.68]:
        beam('Reja de ventana',(cx+.21*w+dx,fy+front*.06,1.15),(cx+.21*w+dx,fy+front*.06,2.17),.014,silver)
    for zz in [1.19,1.65,2.12]:beam('Travesano reja',(cx+.21*w-.77,fy+front*.06,zz),(cx+.21*w+.77,fy+front*.06,zz),.012,silver)
    # Pretil y deposito de agua en algunas azoteas.
    if int(cx)%2==0:
        cyl('Tinaco negro',(cx+.2*w,cy,h+.65),.44,1.0,black,n=20)
        cyl('Tapa tinaco',(cx+.2*w,cy,h+1.18),.47,.08,black,n=20)
for i,x in enumerate([-24,-15,-6,3,12,21]):house(x,-18.35,7.6,6.0,3.1+(i%3)*.5,housecolors[i],front=1)
for i,y in enumerate([1.7,11.0,20.0]):
    house(-22,y,8,7,3.5+(i%2)*1.0,housecolors[(i+2)%6],front=-1)
    house(22,y,8,7,3.2+(i%2)*.5,housecolors[(i+4)%6],front=-1)
for i,x in enumerate([-12,0,12]):house(x,23,9,6,4.0+(i%2),housecolors[(i+1)%6],front=-1)

# Paredes perimetrales fisicas, continuas y colisionables. Nada conduce al vacio.
for name,loc,size in [
    ('Muro perimetral oeste',(-30,2.5,2.4),(.40,49.4,4.8)),
    ('Muro perimetral este',(30,2.5,2.4),(.40,49.4,4.8)),
    ('Muro perimetral sur',(0,-22,2.4),(60.4,.40,4.8)),
    ('Muro perimetral norte',(0,27,2.4),(60.4,.40,4.8))]:box(name,loc,size,cement,collider=True)

# Segunda corona de edificios: oculta horizonte bajo y cualquier limite del suelo.
distant=mat('Edificios lejanos',(.22,.29,.31),.9)
for i in range(-7,8):
    for y in [-43,45]:box('Manzana al fondo',(i*9,y,random.uniform(3,6)),(8,9,random.uniform(8,14)),distant)
for i in range(-4,5):
    for x in [-45,45]:box('Casas al fondo',(x,i*10,3),(9,9,6+random.random()*4),distant)

# Postes y tendido aereo al borde de la calle.
for x in [-25,-8,10,27]:
    cyl('Poste electrico',(x,-3.1,3.4),.10,6.8,cement,n=14)
    box('Cruceta poste',(x,-3.1,6.2),(.12,1.8,.10),wood)
    for yy in [-3.75,-3.1,-2.45]:
        if x<27:
            end={-25:-8,-8:10,10:27}[x]
            prev=(x,yy,6.25)
            for k in range(1,9):
                xx=x+(end-x)*k/8;zz=6.25-.45*math.sin(math.pi*k/8)
                beam('Cable electrico',prev,(xx,yy,zz),.012,black);prev=(xx,yy,zz)
    collision_box('Poste electrico',(x,-3.1,1.5),(.25,.25,3))

# Arboles laterales y macetas junto al acceso.
for x,y in [(-12,-.5),(12,-.5),(-13,16),(13,16),(-27,-12),(27,-12)]:
    cyl('Tronco arbol',(x,y,1.8),.17,3.6,trunk,n=12)
    collision_box('Tronco arbol',(x,y,1.5),(.4,.4,3))
    for dx,dy,dz,rr in [(0,0,3.8,1.4),(-.7,.15,3.6,1),(.65,-.2,4.1,1.1)]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=rr,location=(x+dx,y+dy,dz));bpy.context.object.name='Copa de arbol';bpy.context.object.data.materials.append(plants)

# Guardar cajas en coordenadas Three.js Y-up ANTES de combinar geometria.
bpy.context.view_layer.update()
for o in bpy.context.scene.objects:
    if o.get('collider'):
        vs=[o.matrix_world@Vector(v) for v in o.bound_box]
        mn=[min(v[i] for v in vs) for i in range(3)];mx=[max(v[i] for v in vs) for i in range(3)]
        COLLIDERS.append({'name':o.name,'min':[mn[0],mn[2],-mx[1]],'max':[mx[0],mx[2],-mn[1]]})
collisions={'coordinate_system':'threejs_y_up','player':{'radius':.28,'height':1.65,'spawn':[2,1.65,-.7]},'bounds':{'minX':-30,'maxX':30,'minZ':-27,'maxZ':22},'boxes':COLLIDERS}
with open(os.path.join(OUT,'colliders.json'),'w') as f:json.dump(collisions,f,indent=2)

# Fusionar por material para limitar llamadas de dibujo; conservar logo como textura.
mesh_objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
groups={}
for o in mesh_objects:
    if o.get('preserve_instance'):continue
    key=tuple(m.name if m else '' for m in o.data.materials)
    groups.setdefault(key,[]).append(o)
for mats,objects in groups.items():
    if len(objects)<2:continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name='Grupo estatico — '+(mats[0] if mats else 'sin material')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'colmado-el-bloke.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
print('EXPORT_READY: escena y colliders.json',flush=True)

# Luces de presentacion; se excluyeron del GLB para configurar el visor por separado.
world=bpy.data.worlds.new('Cielo de tarde');bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.52,.67,.80,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
bpy.ops.object.light_add(type='SUN',location=(0,-10,18));sun=bpy.context.object;sun.name='Sol de tarde';sun.rotation_euler=(.52,-.3,-.45);sun.data.energy=2;sun.data.angle=.18
for x in [-5.5,0,5.5]:
    for y in [2,7,10.5]:
        bpy.ops.object.light_add(type='AREA',location=(x,y,4.20));l=bpy.context.object;l.name='Luz interior';l.data.energy=160;l.data.shape='RECTANGLE';l.data.size=3;l.data.size_y=2
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(6.6,.8,2.5));cam=bpy.context.object;cam.data.lens=24;scene.camera=cam

def capture(name,position,target,lens):
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    scene.render.filepath=os.path.join(OUT,name+'.png');bpy.ops.render.render(write_still=True)

cam.location=(7.8,-.8,3.55);cam.data.lens=20
cam.rotation_euler=(Vector((0,5.0,1.0))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'colmado-el-bloke.blend'))
capture('colmado-interior',(7.8,-.8,3.55),(0,5.0,1.0),20)
capture('colmado-calle',(10,-12,3.2),(0,4,2),24)
# Vista elevada de distribucion: ocultar solo el techo de la captura, no del modelo.
roof=bpy.data.objects.get('Techo solido');roof.hide_render=True
capture('distribucion-mesas',(0,5.0,16),(0,5.0,0),30)
roof.hide_render=False
print('DONE: seis mesas, 24 sillas, sin personajes ni fichas',flush=True)
