import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const host=document.getElementById('view');
const loading=document.getElementById('loading');
const loadDetail=document.getElementById('load-detail');
const error=document.getElementById('error');
const playButton=document.getElementById('play');
const restartButton=document.getElementById('restart');
const timeline=document.getElementById('timeline');
const timeOutput=document.getElementById('time');
let mixer=null, primary=null, actions=[], duration=0, currentTime=0;
let playing=false, ready=false, dirty=true, previous=performance.now();

function showError(message,cause){
  playing=false;loading.classList.add('done');error.hidden=false;error.textContent=message;console.error(cause??message);
}

let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});}
catch(cause){showError('Este navegador no pudo iniciar la vista 3D. Prueba con Chrome o Safari actualizado.',cause);throw cause;}
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(innerWidth,innerHeight);
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.05;
renderer.domElement.tabIndex=0;
renderer.domElement.setAttribute('aria-label','Modelo 3D animado. Arrastra para girar la cámara.');
host.prepend(renderer.domElement);

const scene=new THREE.Scene();
scene.background=new THREE.Color('#d8ddd8');
scene.fog=new THREE.Fog('#d8ddd8',12,35);
const camera=new THREE.PerspectiveCamera(48,innerWidth/innerHeight,.04,60);
camera.position.set(2,1.6,-1.6);
const orbit=new OrbitControls(camera,renderer.domElement);
orbit.target.set(0,.85,.4);
// Preserve the complete character/table framing on tall phone screens.
if(camera.aspect<.78){
  const offset=camera.position.clone().sub(orbit.target).multiplyScalar(.78/camera.aspect);
  camera.position.copy(orbit.target).add(offset);
}
orbit.enablePan=false;orbit.enableDamping=false;
orbit.minDistance=1.2;orbit.maxDistance=7;
orbit.minPolarAngle=.08;orbit.maxPolarAngle=Math.PI/2-.035;
orbit.update();orbit.addEventListener('change',()=>dirty=true);

scene.add(new THREE.HemisphereLight('#eef5ff','#7f796a',2));
const key=new THREE.DirectionalLight('#fff1db',2.6);key.position.set(-3,5,-4);scene.add(key);
const rim=new THREE.DirectionalLight('#e8f0ff',1.4);rim.position.set(4,3,3);scene.add(rim);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(80,80),new THREE.MeshStandardMaterial({color:'#bfc6bc',roughness:1}));
floor.rotation.x=-Math.PI/2;floor.position.y=-.025;scene.add(floor);

function updateInterface(){
  timeline.value=String(currentTime);
  const format=n=>n.toFixed(1).replace('.',',');
  timeOutput.textContent=`${format(currentTime)} / ${format(duration)} s`;
  playButton.textContent=playing?'Pausar':currentTime>=duration-.01&&duration?'Repetir':'Reproducir';
  playButton.setAttribute('aria-pressed',String(playing));
  timeline.setAttribute('aria-valuetext',`${format(currentTime)} segundos`);
}

function seek(seconds){
  if(!mixer||!primary)return;
  currentTime=THREE.MathUtils.clamp(Number(seconds)||0,0,duration);
  primary.reset();primary.setLoop(THREE.LoopOnce,1);primary.clampWhenFinished=true;primary.play();
  mixer.setTime(currentTime);
  dirty=true;updateInterface();
}
function play(){
  if(!ready)return;
  if(currentTime>=duration-.01)seek(0);
  playing=true;previous=performance.now();updateInterface();
}
function pause(){playing=false;updateInterface();}
function restart(){seek(0);play();}
playButton.addEventListener('click',()=>playing?pause():play());
restartButton.addEventListener('click',restart);
timeline.addEventListener('input',()=>{
  const requestedTime=timeline.value;
  pause();seek(requestedTime);
});

window.addEventListener('resize',()=>{
  camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);dirty=true;
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();previous=performance.now();});

function animate(now){
  requestAnimationFrame(animate);
  // A play click can arrive after this frame's RAF timestamp was sampled.
  // A negative delta would finish a LoopOnce action backwards at time zero.
  const delta=Math.max(0,Math.min((now-previous)/1000,1));previous=now;
  if(ready&&playing){
    if(currentTime+delta>=duration){seek(duration);pause();}
    else{mixer.update(delta);currentTime=primary.time;updateInterface();dirty=true;}
  }
  if(dirty){renderer.render(scene,camera);dirty=false;}
}
requestAnimationFrame(animate);

try{
  const gltf=await new GLTFLoader().loadAsync('../personaje-domino-animado.glb',progress=>{
    if(progress.total)loadDetail.textContent=`Cargando: ${Math.round(progress.loaded/progress.total*100)} %`;
  });
  scene.add(gltf.scene);
  if(!gltf.animations.length)throw new Error('El archivo no contiene un clip de animación.');
  const chosen=gltf.animations.find(clip=>clip.name==='Domino_Sentarse_Agarrar_Colocar')??gltf.animations[0];
  mixer=new THREE.AnimationMixer(gltf.scene);
  actions=gltf.animations.map(clip=>mixer.clipAction(clip));
  primary=mixer.clipAction(chosen);duration=chosen.duration;
  timeline.max=String(duration);
  playButton.disabled=false;restartButton.disabled=false;timeline.disabled=false;
  ready=true;seek(0);loading.classList.add('done');
  window.dominoAnimation={scene,mixer,actions,camera,renderer,orbit,seek,play,pause,
    get duration(){return duration;},get time(){return currentTime;},get playing(){return playing;},get ready(){return ready;},
    clipName:chosen.name,model:gltf.scene};
  if(!matchMedia('(prefers-reduced-motion:reduce)').matches)play();
}catch(cause){showError('No se pudo abrir la animación. Vuelve a cargar cuando el modelo esté listo.',cause);}
