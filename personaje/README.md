# Personaje humano — sentarse, agarrar y colocar

Demostración 3D con el personaje Casual Male de Manoel da Rocha, la mesa EL BLOKE aprobada y una sola ficha de prueba. No se ha creado el juego completo de fichas.

## Animación

Secuencia de 8 segundos, 240 fotogramas a 30 fps:
- Sentarse: parte de pie y se acomoda en la silla.
- Agarrar: inclina el cuerpo, alcanza la ficha y cierra índice y pulgar.
- Colocar: levanta la ficha, la lleva a otra posición de la mesa, abre la mano y retira el brazo.

La animación original de sentarse se reutilizó del personaje. Los movimientos de alcance, pinza, traslado y retirada se prepararon para esta mesa y se hornearon a claves de huesos. Es una muestra con posiciones predeterminadas; conectarla a las posiciones y turnos reales del juego es un paso posterior de integración.

## Ver

- `personaje-domino-animacion.mp4`: video renderizado del modelo real.
- `personaje-domino-animacion.gif`: vista animada ligera.
- `personaje-domino-animado.glb`: personaje articulado, mesa, silla, ficha y animación.
- La escena editable `personaje-domino-animado.blend` queda incluida en esta carpeta, con luces y cámara. No forma parte del ZIP ligero del visor.
- `viewer/`: visor para reproducir, pausar, arrastrar la vista y revisar el tiempo.

Para usar el visor, sirve esta carpeta con `python -m http.server 8766` y abre `http://localhost:8766/viewer/`. Las bibliotecas están incluidas para no depender de una CDN.

## Procedencia

El personaje original es de Manoel da Rocha y se distribuye bajo CC BY 4.0 en la publicación oficial del autor. Los créditos y enlaces están en `assets/ATTRIBUTION.md`. Los cambios de animación y la mesa se crearon para esta demostración. El logo EL BLOKE es la imagen original aportada por el usuario.

La escena del colmado permanece separada en [`../colmado/`](../colmado/). Los paquetes descargables están en [`../paquetes/`](../paquetes/). Esta demostración no conecta todavía las posiciones de las fichas con partidas multijugador.
