# Recorrido local de El Bloke

Visor del modelo real `../colmado-el-bloke.glb`, con colisiones tomadas de `../colliders.json`.

Desde la carpeta padre de `viewer/`, ejecuta:

```sh
python -m http.server 8765
```

Abrir `http://localhost:8765/viewer/`. No se publica nada. Las dependencias de Three.js 0.170.0 están incluidas y el recorrido no necesita CDN ni conexión a internet.

Controles: W A S D o flechas para caminar; arrastrar para mirar. En móvil, usar la cruceta y deslizar sobre la escena. «Volver al inicio» restablece el punto de entrada.

La cámara mantiene una altura fija: no hay gravedad ni saltos. Las colisiones son cajas estáticas en X/Z, ampliadas por el radio del jugador, con movimiento dividido en subpasos para evitar cruzar muros finos. El mapa tiene límites explícitos; un suelo extendido, cielo continuo y niebla evitan mostrar un borde vacío. Esto es un recorrido de muestra, no una integración con el juego de dominó.

Comprobar la colisión:

```sh
node viewer/test-collision.mjs
```

La prueba de navegador `node viewer/test-browser.cjs` usa Playwright y Chromium. Requiere instalar Playwright en el entorno de desarrollo y mantener el servidor local abierto. Comprueba carga real del GLB, movimiento con teclado, altura fija, límites, arrastre de vista, reinicio y movimiento con un toque sostenido en móvil. Guarda capturas de escritorio y móvil en la carpeta del escenario. Permite indicar `CHROMIUM_EXECUTABLE` y `COLMADO_PREVIEW_URL`.

Para la disposición actual de seis mesas y veinticuatro sillas, `node viewer/check-six-tables.cjs` comprueba el nuevo inicio, el pasillo entre mesas en x=2, la salida a la calle y la carga en escritorio/móvil. Verifica además que el GLB no contenga skins, clips de personajes ni nodos de fichas. El resultado se guarda en `six-tables-check.json` y las capturas del visor en la carpeta del escenario.

Three.js conserva su licencia MIT en `vendor/THREE-LICENSE.txt`.
