# EL BLOKE — colmado, mesa y personaje 3D

Archivos finales del proyecto organizados para abrir las demostraciones y continuar trabajando en Blender o en el motor del juego.

## Abrir las demostraciones

Desde la raíz del repositorio:

```bash
python -m http.server 8080
```

Abre **http://localhost:8080/**. No hace falta instalar dependencias para ver las escenas; Three.js viene incluido.

- [Colmado y barrio](colmado/viewer/): seis mesas, cuatro sillas vacías por mesa, portavasos y ranuras, calle, casas, bocinas y bebidas. Incluye colisiones y 24 puntos de asiento. El colmado no contiene personajes ni fichas.
- [Personaje animado](personaje/viewer/): demostración separada de ocho segundos para sentarse, agarrar una ficha de prueba y colocarla en la mesa EL BLOKE.
- [Video de la animación](personaje/personaje-domino-animacion.mp4).
- [Mesa EL BLOKE](mesa/mesa-el-bloke-sin-fichas.glb), con el logo original y sin fichas.

Los enlaces son relativos y funcionan también si se sirve el proyecto bajo una subcarpeta, por ejemplo `/Elpepe/`.

## Organización

| Carpeta | Contenido |
| --- | --- |
| `colmado/` | Escenario GLB, Blender editable, visores, distribución de asientos, colisiones y fuentes de construcción. |
| `personaje/` | Personaje GLB y Blender animado, video/GIF, visor, animaciones, FBX/texturas originales y créditos. |
| `mesa/` | Mesa GLB y Blender editable, logo original y vistas. |
| `paquetes/` | Los dos ZIP entregados del colmado y del personaje. |

## Comprobar los archivos

```bash
npm test
```

La comprobación valida los modelos y sus recursos, las seis mesas y 24 sillas, la ausencia de personajes en el colmado, la animación de ocho segundos y las colisiones del recorrido.

Para reconstruir el colmado con Blender:

```bash
blender -b -t 8 -P colmado/build_scene.py
```

Para reconstruir la demostración del personaje:

```bash
blender -b -t 8 -P personaje/build_animation.py
```

Los `.blend` finales contienen los recursos empaquetados y pueden editarse directamente. Los scripts resuelven sus recursos dentro del repositorio.

## Estado del proyecto

Son demostraciones 3D funcionales con posiciones preparadas. La lógica multijugador, los turnos y las jugadas del dominó deben conectarse por separado. Mantener el personaje separado del colmado es intencional: sus 24 sillas siguen vacías.

## Créditos

El personaje original Casual Male es de Manoel da Rocha y se publica bajo CC BY 4.0. Se modificaron sus animaciones para la demostración; [créditos y procedencia](personaje/assets/ATTRIBUTION.md). Three.js está incluido bajo su [licencia MIT](colmado/viewer/vendor/THREE-LICENSE.txt). El logo EL BLOKE fue aportado por el usuario.
