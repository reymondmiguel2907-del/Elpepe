import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createCollisionWorld} from '../colmado/viewer/collision.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
function glb(relative){
  const bytes=fs.readFileSync(path.join(root,relative));
  assert.equal(bytes.toString('ascii',0,4),'glTF');
  assert.equal(bytes.readUInt32LE(4),2);
  assert.equal(bytes.readUInt32LE(8),bytes.length);
  const length=bytes.readUInt32LE(12);
  const data=JSON.parse(bytes.subarray(20,20+length).toString());
  for(const image of data.images??[]){
    if(image.uri&&!image.uri.startsWith('data:'))assert.ok(fs.existsSync(path.resolve(root,path.dirname(relative),image.uri)),`Textura ausente: ${image.uri}`);
  }
  return data;
}
const shop=glb('colmado/colmado-el-bloke.glb');
const nodes=shop.nodes??[];
assert.equal(nodes.filter(n=>n.name?.endsWith('/ mesa domino')).length,6);
assert.equal(nodes.filter(n=>n.name?.endsWith('/ silla vacia')).length,24);
assert.equal(nodes.filter(n=>n.name?.endsWith('/ punto de asiento')).length,24);
assert.equal(shop.skins?.length??0,0);
assert.equal(shop.animations?.length??0,0);
assert.ok(!nodes.some(n=>/^(Rig|casual_male|Ficha)/i.test(n.name??'')));
const layout=JSON.parse(fs.readFileSync(path.join(root,'colmado/seating-layout.json')));
assert.equal(layout.table_count,6);assert.equal(layout.chair_count,24);
assert.equal(layout.characters_included,false);
for(const table of layout.tables){
  assert.equal(table.seats.length,4);
  assert.equal(new Set(table.seats.map(s=>s.side)).size,4);
  assert.ok(table.seats.every(s=>s.occupied===false));
}
const colliders=JSON.parse(fs.readFileSync(path.join(root,'colmado/colliders.json')));
assert.equal(colliders.boxes.length,87);
const world=createCollisionWorld(colliders);
const spawn=world.safeSpawn(colliders.player.spawn);
assert.ok(Math.abs(spawn.x-colliders.player.spawn[0])<.001);
assert.ok(Math.abs(spawn.z-colliders.player.spawn[2])<.001);
const actor=glb('personaje/personaje-domino-animado.glb');
assert.ok(actor.skins?.length>0);
assert.equal(actor.animations.length,1);
const clip=actor.animations[0];
const duration=Math.max(...clip.samplers.map(s=>actor.accessors[s.input].max?.[0]??0));
assert.ok(Math.abs(duration-8)<.05,`Duración inesperada: ${duration}`);
const table=glb('mesa/mesa-el-bloke-sin-fichas.glb');
assert.ok(!table.nodes.some(n=>/Ficha/i.test(n.name??'')));
for(const file of ['index.html','styles.css','personaje/assets/ATTRIBUTION.md','colmado/viewer/vendor/THREE-LICENSE.txt','personaje/viewer/vendor/THREE-LICENSE.txt','paquetes/colmado-el-bloke-completo.zip','paquetes/domino-character-animation-completo.zip'])assert.ok(fs.existsSync(path.join(root,file)),`Archivo ausente: ${file}`);
console.log('PASS: modelos, texturas, seis mesas, 24 sillas vacías, colisiones y animación de ocho segundos.');
