const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const assetRoot=path.resolve(__dirname,'..');
const previewURL=process.env.DOMINO_ANIMATION_URL||('http://127.0.0.1:8766/viewer/?v='+Date.now());

(async()=>{
  const browser=await chromium.launch({
    executablePath:process.env.CHROMIUM_EXECUTABLE||'/usr/bin/chromium',headless:true,
    args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox']
  });
  const errors=[];
  const context=await browser.newContext({viewport:{width:1000,height:800},deviceScaleFactor:1});
  const page=await context.newPage();
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(previewURL,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.dominoAnimation?.ready,null,{timeout:120000});
  const loaded=await page.evaluate(()=>{
    const d=window.dominoAnimation;d.pause();d.seek(0);
    let skinnedMeshes=0,bones=0;
    d.model.traverse(o=>{if(o.isSkinnedMesh)skinnedMeshes++;if(o.isBone)bones++;});
    return {duration:d.duration,clip:d.clipName,skinnedMeshes,bones};
  });
  assert(loaded.duration>0);
  assert(loaded.skinnedMeshes>0,'El archivo debe contener una malla articulada.');
  console.log('LOADED',JSON.stringify(loaded));
  const poses=await page.evaluate(()=>{
    const d=window.dominoAnimation;
    const pose=time=>{
      d.seek(time);d.model.updateMatrixWorld(true);
      const values=[];
      d.model.traverse(o=>{if(o.isBone)values.push(...o.matrixWorld.elements);});
      return values;
    };
    const first=pose(0),middle=pose(d.duration*.6);
    return {difference:first.reduce((sum,x,i)=>sum+Math.abs(x-middle[i]),0),time:d.time};
  });
  assert(poses.difference>.05,'Cambiar el tiempo debe mover el esqueleto real.');
  console.log('POSES',JSON.stringify(poses));
  await page.evaluate(()=>{const d=dominoAnimation;d.seek(0);d.play();});
  await page.waitForFunction(()=>dominoAnimation.time>.2,null,{timeout:45000}).catch(async error=>{console.log('PLAYBACK STATE',JSON.stringify(await page.evaluate(()=>({time:dominoAnimation.time,playing:dominoAnimation.playing,hidden:document.hidden,mixerTime:dominoAnimation.mixer.time,actions:dominoAnimation.actions.map(a=>({time:a.time,paused:a.paused,enabled:a.enabled,timeScale:a.timeScale}))}))));throw error;});
  const pausedTime=await page.evaluate(()=>{dominoAnimation.pause();return dominoAnimation.time;});
  await page.waitForTimeout(350);
  assert.equal(await page.evaluate(()=>dominoAnimation.time),pausedTime,'Pausa conserva el tiempo.');
  await page.evaluate(()=>{
    const input=document.getElementById('timeline');
    input.value=String(dominoAnimation.duration*.55);input.dispatchEvent(new Event('input',{bubbles:true}));
  });
  const scrub=await page.evaluate(()=>({time:dominoAnimation.time,duration:dominoAnimation.duration,playing:dominoAnimation.playing}));
  assert(Math.abs(scrub.time-scrub.duration*.55)<.02);
  assert.equal(scrub.playing,false);
  console.log('SCRUB',JSON.stringify(scrub));
  await page.screenshot({path:path.join(assetRoot,'preview-personaje-desktop.png'),timeout:120000});
  for(const time of [2,4.5,6.4]){
    await page.evaluate(seconds=>{dominoAnimation.pause();dominoAnimation.seek(seconds);},time);
    await page.screenshot({path:path.join(assetRoot,`preview-pose-${String(time).replace('.','_')}s.png`),timeout:120000});
    console.log('CAPTURE',JSON.stringify({time,file:`preview-pose-${String(time).replace('.','_')}s.png`}));
  }
  const beforeOrbit=await page.evaluate(()=>dominoAnimation.camera.position.toArray());
  await page.mouse.move(500,300);await page.mouse.down();await page.mouse.move(630,320,{steps:3});await page.mouse.up();
  const afterOrbit=await page.evaluate(()=>dominoAnimation.camera.position.toArray());
  assert(Math.hypot(...beforeOrbit.map((x,i)=>x-afterOrbit[i]))>.1,'Arrastrar debe cambiar la cámara.');
  await page.click('#restart');
  await page.waitForFunction(()=>dominoAnimation.playing&&dominoAnimation.time<1,null,{timeout:10000});
  await page.evaluate(()=>dominoAnimation.pause());
  console.log('DESKTOP PASS: clip real, esqueleto, reproducción, pausa, barra, órbita y reinicio');

  const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
  const mp=await mobile.newPage();
  mp.on('pageerror',error=>errors.push(error.message));
  await mp.goto(previewURL,{waitUntil:'domcontentloaded'});
  await mp.waitForFunction(()=>window.dominoAnimation?.ready,null,{timeout:120000});
  await mp.evaluate(()=>{dominoAnimation.pause();dominoAnimation.seek(dominoAnimation.duration*.55);});
  assert(await mp.locator('#controls').isVisible());
  const box=await mp.locator('#controls').boundingBox();
  assert(box.x>=0&&box.x+box.width<=391,'Los controles deben caber en móvil.');
  await mp.screenshot({path:path.join(assetRoot,'preview-personaje-mobile.png'),timeout:120000});
  console.log('MOBILE PASS: carga y controles dentro de la pantalla');
  assert.equal(errors.length,0,errors.join('\n'));
  console.log('PASS: sin errores JavaScript');
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
