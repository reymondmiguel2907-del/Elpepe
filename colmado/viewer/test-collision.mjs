import assert from 'node:assert/strict';
import {createCollisionWorld} from './collision.mjs';

const data={
  player:{radius:.28,height:1.65,spawn:[0,1.65,0]},
  bounds:{minX:-10,maxX:10,minZ:-10,maxZ:10},
  boxes:[
    {name:'Pared muy fina',min:[2,0,-4],max:[2.03,3,4]},
    {name:'Muro norte',min:[-4,0,-5],max:[4,3,-4.9]},
    {name:'Suelo no bloqueante',min:[-100,-.1,-100],max:[100,0,100]},
    {name:'Viga por encima de la cabeza',min:[-5,3,-5],max:[5,3.2,5]},
  ],
};
const world=createCollisionWorld(data);
assert.deepEqual(world.safeSpawn(data.player.spawn),{x:0,z:0});
const fast=world.move({x:0,z:0},9,0);
assert(fast.x<=1.72,'Un movimiento muy grande no puede atravesar una pared fina.');
const slide=world.move({x:1.7,z:0},2,2);
assert(slide.x<=1.72 && slide.z>1.8,'Debe deslizarse junto a la pared.');
const around=world.move({x:0,z:5},8,0);
assert(around.x>7.9,'Se puede rodear el extremo de un muro.');
const edge=world.move({x:0,z:6},100,100);
assert(edge.x<=9.72 && edge.z<=9.72,'Los límites conservan el cuerpo dentro del mapa.');
const badSpawn=world.safeSpawn([2,1.65,0]);
assert(world.isFree(badSpawn.x,badSpawn.z),'Un inicio dentro de una pared se corrige.');
assert.equal(world.boxCount,2,'El suelo y las vigas elevadas no bloquean caminar.');
console.log('PASS: paredes finas, deslizamiento, rodear obstáculos, límites, inicio seguro y altura.');
