# Prueba local del personaje animado

Carga el archivo real `../personaje-domino-animado.glb`. Reproduce el clip `Domino_Sentarse_Agarrar_Colocar` o, si no existe ese nombre, el primer clip disponible.

Desde la carpeta padre de `viewer/`, ejecuta:

```sh
python -m http.server 8766 --bind 127.0.0.1
```

Abrir `http://127.0.0.1:8766/viewer/`. No se publica nada. Three.js 0.170.0, GLTFLoader y OrbitControls están incluidos localmente con su licencia MIT.

Controles:
- Reproducir o pausar la secuencia.
- Volver al principio con «Desde el inicio».
- Mover la barra para revisar cualquier segundo; al hacerlo se pausa.
- Arrastrar para girar alrededor del personaje y la mesa.
- Rueda o pellizco para acercarse.

Diagnóstico: `window.dominoAnimation` expone la escena, mixer, acciones, cámara, duración, tiempo y funciones `seek`, `play` y `pause` para revisar poses. En pausa, solo se vuelve a dibujar al cambiar el encuadre o el tiempo.

El visor muestra el modelo y sus movimientos reales. No modifica ni publica el juego de dominó.

Con Playwright instalado y el servidor abierto, `node viewer/test-browser.cjs` verifica que el GLB contenga un esqueleto real que cambie de pose, reproducción y pausa, barra de tiempo, reinicio, órbita y carga en móvil. Guarda capturas en la carpeta del modelo. Se pueden indicar `CHROMIUM_EXECUTABLE` y `DOMINO_ANIMATION_URL`.
