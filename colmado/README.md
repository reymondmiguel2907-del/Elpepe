# Colmado EL BLOKE — escena 3D y recorrido local

Colmado de 18 × 12 metros, con frente amplio abierto a una calle y casas de barrio alrededor. Construido como modelo 3D real en Blender, con visor de recorrido en navegador.

Incluye:
- Dos grupos de bocinas grandes con conos modelados.
- Neveras, barra, estantes y botellas estilizadas de Presidente, Brugal Extra Viejo y Fireball. Los nombres de las marcas se modelaron como texto; no son reproducciones exactas de las etiquetas comerciales.
- Seis mesas EL BLOKE con el logo original, cuatro portavasos y ranuras por mesa, sin fichas.
- Cuatro sillas vacías por mesa: 24 sillas orientadas hacia el centro de su mesa, con pasillos para caminar.
- Veinticuatro marcadores de asiento vacíos para colocar personajes después. No se importó ningún personaje ni esqueleto.
- Cajas, iluminación de techo, aceras, casas con rejas, tinacos, postes, cables y árboles.
- Piso continuo, cuatro muros perimetrales y edificios exteriores que cierran visualmente el mundo.
- Colisiones en el recorrido: muros, casas, mostrador, neveras y otros obstáculos. El movimiento usa altura fija y no permite caer ni cruzar los límites del área.

## Recorrer en tu navegador

1. Extrae el paquete completo.
2. Abre una terminal dentro de esta carpeta.
3. Ejecuta `python -m http.server 8765`.
4. Abre `http://localhost:8765/viewer/`.

En computadora: W A S D o flechas para caminar; arrastra la vista para mirar. En móvil: botones de dirección y arrastrar para mirar. El botón de volver al inicio devuelve al acceso del colmado.

No basta con abrir el HTML mediante `file://`; el navegador necesita el servidor local para cargar el modelo. Las librerías del visor vienen incluidas y no dependen de una CDN.

## Archivos
- `colmado-el-bloke.glb`: escenario y materiales, sin cámaras ni luces de estudio; el visor añade sus luces.
- `colliders.json`: obstáculos, límites y punto de inicio, en coordenadas Three.js Y-up.
- `seating-layout.json`: las seis mesas y sus cuatro asientos, con posición, orientación y estado vacío.
- `colmado-el-bloke.blend`: escena editable con luces y cámaras de presentación.
- `colmado-interior.png`, `colmado-calle.png`, `distribucion-mesas.png`: vistas actualizadas del modelo real y la distribución de mesas/sillas. La vista de distribución recorta el techo únicamente en la cámara de presentación.
- `viewer/`: recorrido local con controles de computadora y móvil.
- `build_scene.py`, `beverage_props.py`, `seating_layout.py` y `assets/`: fuentes para reproducir el modelo con Blender. `render_seating_views.py` permite sacar las nuevas vistas desde el Blender guardado.

Para reconstruir: `blender -b -t 8 -P build_scene.py`.

## Alcance

Es una escena nueva y un recorrido local. No se ha integrado, subido ni publicado en el repositorio del juego. No contiene fichas ni personajes. La iluminación de los renders de Blender difiere de la iluminación del visor y deberá ajustarse durante la integración final al juego.

## Verificación

El archivo GLB carga con su logo incluido. El recorrido usa subpasos de movimiento para impedir atravesar paredes finas, frena ante obstáculos y mantiene una altura constante. Se comprobó que el inicio está libre, se puede salir a la calle y que desplazamientos grandes en múltiples direcciones no permiten escapar del perímetro.

La distribución actual tiene 6 mesas, 24 sillas y 24 puntos de asiento. Se verificó que cada mesa tiene un asiento por lado, que todos miran hacia el centro y que los puntos de acceso detrás de las 24 sillas son alcanzables. El archivo exportado no contiene personajes, esqueletos, animaciones ni fichas. Las copias comparten geometría para mantener ligero el modelo.
