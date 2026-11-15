"""Stylized beverage display for the EL BLOKE colmado. Blender bpy module.

Coordinates: interior x[-9,9], y[0,12], front faces negative Y.
Brand names are modeled text, not copied label artwork. No lights/cameras.
"""
import bpy
import math


def _mat(name, color, rough=.48, metal=0):
    name = 'Bebidas / ' + name
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


def _box(name, location, dimensions, material, bevel=.01, collider=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    o = bpy.context.object
    o.name = 'Bebidas / ' + name
    o.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new('Bordes suaves', 'BEVEL')
        b.width = bevel
        b.segments = 2
        bpy.ops.object.modifier_apply(modifier=b.name)
    if collider:
        o['collider'] = True
        o['collision_type'] = 'aabb'
    return o


def _text(body, loc, size, mat, name='Rotulo', extrude=.0001):
    bpy.ops.object.text_add(location=loc, rotation=(math.pi/2, 0, 0))
    o = bpy.context.object
    o.name = 'Bebidas / ' + name
    o.data.body = body
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    o.data.size = size
    o.data.extrude = extrude
    o.data.materials.append(mat)
    bpy.ops.object.convert(target='MESH')
    return o


def _lathe(name, profile, material, segments=20):
    vertices=[]
    for z, radius in profile:
        vertices.extend([(radius*math.cos(2*math.pi*i/segments),
                          radius*math.sin(2*math.pi*i/segments), z)
                         for i in range(segments)])
    faces=[]
    for ring in range(len(profile)-1):
        for i in range(segments):
            j=(i+1)%segments
            faces.append((ring*segments+i,ring*segments+j,
                          (ring+1)*segments+j,(ring+1)*segments+i))
    faces.append(tuple(reversed(range(segments))))
    start=(len(profile)-1)*segments
    faces.append(tuple(start+i for i in range(segments)))
    me=bpy.data.meshes.new(name)
    me.from_pydata(vertices,[],faces)
    me.update()
    o=bpy.data.objects.new('Bebidas / '+name,me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth=len(p.vertices)==4
    return o


def _label(name, radius, bottom, top, material, span=1.95):
    vs=[]
    steps=12
    for z in [bottom,top]:
        vs.extend([(radius*math.cos(-math.pi/2-span/2+span*i/steps),
                    radius*math.sin(-math.pi/2-span/2+span*i/steps),z)
                   for i in range(steps+1)])
    fs=[(i,i+1,steps+2+i,steps+1+i) for i in range(steps)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    o=bpy.data.objects.new('Bebidas / '+name,me)
    bpy.context.collection.objects.link(o);o.data.materials.append(material)
    return o


def _bottle(kind, materials):
    green, amber, cream, red, blue, gold, white, black = materials
    if kind=='Presidente':
        profile=[(0,.037),(.012,.043),(.20,.043),(.235,.033),(.26,.019),(.323,.017),(.33,.018)]
        bodymat=green;capmat=gold;labelmat=cream
        name='Presidente'
    elif kind=='Brugal':
        profile=[(0,.043),(.012,.048),(.205,.048),(.24,.039),(.265,.022),(.35,.02),(.36,.022)]
        bodymat=amber;capmat=gold;labelmat=blue
        name='Brugal Extra Viejo'
    else:
        profile=[(0,.043),(.012,.048),(.205,.048),(.245,.035),(.268,.022),(.315,.021),(.325,.023)]
        bodymat=amber;capmat=red;labelmat=cream
        name='Fireball'
    parts=[_lathe(name+' botella',profile,bodymat)]
    h=profile[-1][0];r=profile[-1][1]
    parts.append(_lathe(name+' tapa',[(h-.023,r*1.03),(h+.007,r*1.03)],capmat))
    radius=.0436 if kind=='Presidente' else .0486
    if kind=='Presidente':
        parts.append(_label(name+' etiqueta',radius,.083,.185,labelmat))
        parts.append(_text('PRESIDENTE',(0,-radius-.0015,.148),.0108,green,name+' marca'))
        parts.append(_text('CERVEZA',(0,-radius-.0015,.121),.0084,red,name+' cerveza'))
        parts.append(_text('DOMINICANA',(0,-radius-.0015,.102),.0067,green,name+' origen'))
        parts.append(_label(name+' cuello',.0195,.271,.305,cream,span=2.3))
    elif kind=='Brugal':
        parts.append(_label(name+' etiqueta',radius,.085,.205,labelmat))
        parts.append(_text('BRUGAL',(0,-radius-.0015,.169),.016,white,name+' marca'))
        parts.append(_text('EXTRA VIEJO',(0,-radius-.0015,.135),.0095,gold,name+' variedad'))
        parts.append(_text('RON DOMINICANO',(0,-radius-.0015,.109),.0062,white,name+' origen'))
        # Stylized gold bands hint at the characteristic bottle netting.
        parts.append(_lathe(name+' banda inferior',[(.052,.0490),(.059,.0490)],gold))
        parts.append(_lathe(name+' banda superior',[(.214,.045),(.219,.044)],gold))
    else:
        parts.append(_label(name+' etiqueta',radius,.074,.211,labelmat))
        parts.append(_text('FIREBALL',(0,-radius-.0015,.167),.014,red,name+' marca'))
        parts.append(_text('CINNAMON',(0,-radius-.0015,.123),.0074,black,name+' canela'))
        parts.append(_text('WHISKY',(0,-radius-.0015,.101),.0085,black,name+' whisky'))
        parts.append(_text('HOT',(0,-radius-.0015,.143),.008,red,name+' hot'))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
    o=bpy.context.object
    o.name='Bebidas / '+name+' modelo'
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    o['brand']=name
    o['stylized_representation']=True
    return o


def build_beverage_display():
    """Build bar, shelving, signs, and linked bottle meshes; return new objects."""
    before=set(bpy.context.scene.objects)
    green=_mat('Vidrio verde Presidente',(.022,.22,.044),.24,.08)
    amber=_mat('Vidrio ambar',(.31,.105,.019),.25,.05)
    cream=_mat('Papel crema',(.87,.81,.62),.75)
    red=_mat('Rojo etiqueta y tapas',(.55,.018,.01),.49)
    blue=_mat('Azul Brugal',(.014,.043,.16),.49)
    gold=_mat('Dorado',(.52,.33,.06),.34,.55)
    white=_mat('Blanco letras',(.95,.93,.85),.75)
    black=_mat('Negro letras',(.009,.009,.009),.8)
    wood=_mat('Madera mostrador',(.16,.064,.025),.57)
    top=_mat('Encimera negra',(.018,.024,.022),.35)
    shelf=_mat('Estanteria verde oscuro',(.018,.083,.061),.55,.2)
    crate=_mat('Cajas verdes Presidente',(.018,.25,.048),.64)
    materials=(green,amber,cream,red,blue,gold,white,black)

    # Counter leaves a broad 5+ metre central circulation area.
    _box('Mostrador colisionable',(5,8.9,.505),(6,1,1.01),wood,.025,True)
    _box('Encimera',(5,8.9,1.045),(6.12,1.12,.08),top,.025)
    _box('Panel frontal',(5,8.386,.56),(5.7,.02,.60),green,.008)
    _text('PRESIDENTE  ·  BRUGAL  ·  FIREBALL',(5,8.368,.57),.185,white,'Rotulo del mostrador',.001)
    _box('Zocalo',(5,8.38,.12),(5.75,.035,.12),top,.005)

    # Three separate bays make all requested brands legible from the shop.
    centres=[.85,3.6,6.35]
    for x in [-.46,2.18,4.92,7.72]:
        _box('Montante estante',(x,11.65,1.82),(.065,.22,2.46),shelf,.009,True)
    for z in [1.4,2.0,2.6]:
        _box('Estante botellas',(3.62,11.63,z),(8.26,.53,.06),shelf,.008)
    _box('Fondo estanteria',(3.62,11.94,1.99),(8.27,.05,1.98),shelf,.008,True)
    for x,brand,color in zip(centres,['PRESIDENTE','BRUGAL','FIREBALL'],[green,blue,red]):
        _box('Cartel '+brand,(x,11.58,3.14),(2.48,.07,.42),color,.018)
        _text(brand,(x,11.536,3.17),.255,white,'Cartel '+brand,.001)
        if brand=='BRUGAL':
            _text('EXTRA VIEJO',(x,11.535,3.025),.095,gold,'Cartel Extra Viejo',.0005)

    templates={brand:_bottle(brand,materials) for brand in ['Presidente','Brugal','Fireball']}
    first={brand:True for brand in templates}
    def put(brand,x,y,z,angle=0,scale=1):
        template=templates[brand]
        if first[brand]:
            o=template;first[brand]=False
        else:
            o=template.copy();o.data=template.data
            bpy.context.collection.objects.link(o)
        o.name='Bebidas / '+brand+' exhibida'
        o.location=(x,y,z);o.rotation_euler[2]=angle;o.scale=(scale,)*3
        return o

    # 45 bottles on shelves, five per brand on each shelf.
    for brand,xcenter in zip(['Presidente','Brugal','Fireball'],centres):
        for z in [1.431,2.031,2.631]:
            for i in range(5):
                put(brand,xcenter+(i-2)*.30,11.52,z,scale=1.14)
    # Counter service bottles grouped, keeping their text facing the room.
    for brand,xcenter in [('Presidente',3.25),('Brugal',5),('Fireball',6.75)]:
        for i in range(3):
            put(brand,xcenter+(i-1)*.17,8.72,1.086,scale=1.18)
    # Green beer crates stored beneath the left part of the display.
    for x,z in [(.2,.22),(.2,.64),(1.0,.22)]:
        _box('Caja de cerveza',(x,10.65,z),(.65,.48,.38),crate,.02,True)
        _box('Asa caja',(x,10.397,z+.1),(.26,.012,.065),black,.012)
        _text('PRESIDENTE',(x,10.392,z-.04),.073,white,'Caja Presidente',.0002)
    bpy.context.scene.cursor.location=(0,0,0)
    return [o for o in bpy.context.scene.objects if o not in before]
