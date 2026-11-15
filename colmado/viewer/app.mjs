import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {createCollisionWorld} from './collision.mjs';

const container = document.getElementById('view');
const loading = document.getElementById('loading');
const detail = document.getElementById('load-detail');
const error = document.getElementById('error');
const keys = new Set();
const touchMoves = new Map();
let world, spawn, ready = false;
let yaw = 0, pitch = 0;
let drag = null;
let lastTime = performance.now();
let needsRender = true;

function showError(message, cause) {
  ready = false;
  loading.classList.add('done');
  error.hidden = false;
  error.textContent = message;
  console.error(cause ?? message);
}

let renderer;
try {
  renderer = new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
} catch (cause) {
  showError('Este navegador no pudo iniciar la vista 3D. Prueba con Chrome o Safari actualizado.', cause);
  throw cause;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
renderer.domElement.tabIndex = 0;
renderer.domElement.setAttribute('aria-label','Vista 3D. Arrastra para mirar; usa las flechas o W A S D para moverte.');
container.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color('#b6c5cf');
scene.fog = new THREE.Fog('#b6c5cf', 38, 105);
const camera = new THREE.PerspectiveCamera(65, window.innerWidth/window.innerHeight, .06, 180);
camera.rotation.order = 'YXZ';
camera.position.set(0,1.65,-3);
camera.rotation.y = yaw;

scene.add(new THREE.HemisphereLight('#e8f3ff', '#8c8872', 2.0));
const sun = new THREE.DirectionalLight('#fff0d8', 2.4);
sun.position.set(-15,25,12);
scene.add(sun);

// Extends beyond the enclosed playable floor, so no camera angle reveals an edge.
const fallbackGround = new THREE.Mesh(
  new THREE.PlaneGeometry(600,600),
  new THREE.MeshStandardMaterial({color:'#777b6c',roughness:1})
);
fallbackGround.rotation.x = -Math.PI/2;
fallbackGround.position.y = -.15;
scene.add(fallbackGround);

function resetView() {
  if (!world || !spawn) return;
  camera.position.set(spawn.x, world.eyeHeight, spawn.z);
  yaw = 0; pitch = 0;
  camera.rotation.set(pitch,yaw,0);
  keys.clear(); touchMoves.clear();
  needsRender = true;
}
document.getElementById('reset').addEventListener('click', resetView);

window.addEventListener('keydown', event => {
  if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(event.key)) event.preventDefault();
  keys.add(event.code);
});
window.addEventListener('keyup', event => keys.delete(event.code));
window.addEventListener('blur', () => {keys.clear();touchMoves.clear();drag=null;});
document.addEventListener('visibilitychange', () => {
  keys.clear(); touchMoves.clear(); drag=null; lastTime=performance.now();
});

const canvas = renderer.domElement;
canvas.addEventListener('pointerdown', event => {
  if (event.button !== 0 && event.pointerType === 'mouse') return;
  drag = {id:event.pointerId,x:event.clientX,y:event.clientY};
  canvas.setPointerCapture(event.pointerId);
  canvas.focus({preventScroll:true});
});
canvas.addEventListener('pointermove', event => {
  if (!drag || drag.id !== event.pointerId) return;
  yaw -= (event.clientX-drag.x)*.004;
  pitch = THREE.MathUtils.clamp(pitch-(event.clientY-drag.y)*.003, -1.15, 1.15);
  drag.x=event.clientX;drag.y=event.clientY;
  needsRender = true;
});
for (const eventType of ['pointerup','pointercancel','lostpointercapture']) {
  canvas.addEventListener(eventType,event=>{if(drag?.id===event.pointerId)drag=null;});
}
canvas.addEventListener('contextmenu', event=>event.preventDefault());

for (const button of document.querySelectorAll('[data-move]')) {
  button.addEventListener('pointerdown',event=>{
    event.preventDefault();
    touchMoves.set(event.pointerId, button.dataset.move);
    button.classList.add('active');
    button.setPointerCapture(event.pointerId);
  });
  const release = event=>{
    touchMoves.delete(event.pointerId);
    button.classList.remove('active');
  };
  button.addEventListener('pointerup',release);
  button.addEventListener('pointercancel',release);
  button.addEventListener('lostpointercapture',release);
}

window.addEventListener('resize',()=>{
  camera.aspect=window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth,window.innerHeight);
  needsRender = true;
});

function animate(time) {
  requestAnimationFrame(animate);
  const dt=Math.min((time-lastTime)/1000,.05);
  lastTime=time;
  if (ready) {
    const touch = new Set(touchMoves.values());
    let forward=Number(keys.has('KeyW')||keys.has('ArrowUp')||touch.has('forward')) - Number(keys.has('KeyS')||keys.has('ArrowDown')||touch.has('backward'));
    let right=Number(keys.has('KeyD')||keys.has('ArrowRight')||touch.has('right')) - Number(keys.has('KeyA')||keys.has('ArrowLeft')||touch.has('left'));
    const magnitude=Math.hypot(forward,right);
    if(magnitude){forward/=magnitude;right/=magnitude;}
    const speed=3.0;
    const dx=(-Math.sin(yaw)*forward+Math.cos(yaw)*right)*speed*dt;
    const dz=(-Math.cos(yaw)*forward-Math.sin(yaw)*right)*speed*dt;
    const next=world.move({x:camera.position.x,z:camera.position.z},dx,dz);
    if(next.x!==camera.position.x || next.z!==camera.position.z) needsRender=true;
    camera.position.set(next.x,world.eyeHeight,next.z);
    camera.rotation.set(pitch,yaw,0);
  }
  // This preview is a static set: redraw only when the view changes.
  // Keeps idle mobile devices cool and avoids queuing unnecessary GPU work.
  if(needsRender){renderer.render(scene,camera);needsRender=false;}
}
requestAnimationFrame(animate);

try {
  const [data, gltf] = await Promise.all([
    fetch('../colliders.json').then(response=>{
      if(!response.ok)throw new Error('No se encontró el recorrido de colisiones.');
      return response.json();
    }),
    new GLTFLoader().loadAsync('../colmado-el-bloke.glb',progress=>{
      if(progress.total)detail.textContent=`Cargando el escenario: ${Math.round(progress.loaded/progress.total*100)} %`;
    }),
  ]);
  world=createCollisionWorld(data);
  spawn=world.safeSpawn(data.player?.spawn);
  gltf.scene.traverse(object=>{
    if(object.isMesh){object.frustumCulled=true;}
  });
  scene.add(gltf.scene);
  resetView();
  ready=true;
  detail.textContent='Listo para recorrer';
  loading.classList.add('done');
  // Read-only diagnostics for local validation, without adding product controls.
  window.colmadoPreview={scene,camera,world,resetView,renderer,get ready(){return ready;}};
} catch(cause) {
  showError('No se pudo abrir el recorrido. Vuelve a cargar la página cuando el escenario esté listo.',cause);
}
