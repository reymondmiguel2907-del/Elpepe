"""Render the real Blender character animation and encode a portable preview.

Run after personaje-domino-animado.blend exists:
  blender -b -t 8 -P render_preview.py -- --benchmark-only
  blender -b -t 8 -P render_preview.py -- --skip-benchmark

The authored animation is sampled at original frames 1,3,...,239 (30 fps),
then encoded at 15 fps so its 8-second timing is preserved.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'personaje-domino-animado.blend'


def options():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-only', action='store_true')
    parser.add_argument('--skip-benchmark', action='store_true')
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)
    parser.add_argument('--samples', type=int)
    return parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def configure(scene, width, height, samples):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = False
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.compression = 15
    scene.render.film_transparent = False
    # This controls encoding only; frame_set continues to use the authored keys.
    scene.render.fps = 15
    scene.render.fps_base = 1


def render_frame(scene, frame, path):
    scene.frame_set(frame)
    scene.render.filepath = str(path)
    started = time.monotonic()
    bpy.ops.render.render(write_still=True)
    elapsed = time.monotonic() - started
    print(f'PREVIEW_FRAME source={frame} elapsed={elapsed:.3f}s file={path}', flush=True)
    return elapsed


def encode(frames_dir):
    video = ROOT / 'personaje-domino-animacion.mp4'
    gif = ROOT / 'personaje-domino-animacion.gif'
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y', '-threads', '2',
        '-framerate', '15', '-start_number', '1',
        '-i', str(frames_dir / 'frame_%04d.png'),
        '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '20',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video),
    ], check=True)
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y', '-threads', '2',
        '-filter_complex_threads', '2', '-i', str(video),
        '-filter_complex',
        'fps=12,scale=360:-1:flags=lanczos,split[a][b];'
        '[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
        '-loop', '0', str(gif),
    ], check=True)
    return video, gif


def main():
    args = options()
    if not SOURCE.is_file():
        raise FileNotFoundError(f'Wait for the completed source scene: {SOURCE}')
    source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    if scene.camera is None:
        raise RuntimeError('The completed scene must have its presentation camera.')
    settings_path = ROOT / 'preview-render-settings.json'
    chosen = {'width': 640, 'height': 480, 'samples': 6}
    if args.skip_benchmark and settings_path.exists():
        chosen.update(json.loads(settings_path.read_text())['settings'])
    if not args.skip_benchmark:
        configure(scene, **chosen)
        bench = ROOT / 'benchmark'
        bench.mkdir(exist_ok=True)
        timings = []
        for frame in (1, 120, 200):
            seconds = render_frame(scene, frame, bench / f'frame_{frame:04d}.png')
            timings.append({'frame': frame, 'seconds': seconds})
        if max(item['seconds'] for item in timings) > 5:
            chosen = {'width': 480, 'height': 360, 'samples': 4}
        settings_path.write_text(json.dumps({
            'source': SOURCE.name,
            'benchmark': timings,
            'settings': chosen,
            'source_fps': 30,
            'source_frames': [1, 239],
            'step': 2,
            'output_fps': 15,
            'duration_seconds': 8,
        }, indent=2))
        print('PREVIEW_SETTINGS ' + json.dumps(chosen), flush=True)
    if args.benchmark_only:
        return
    for key in ('width', 'height', 'samples'):
        if getattr(args, key) is not None:
            chosen[key] = getattr(args, key)
    configure(scene, **chosen)
    frames = ROOT / 'frames'
    frames.mkdir(exist_ok=True)
    # Prevent stale higher-numbered frames from extending a previous sequence.
    for old in frames.glob('frame_*.png'):
        old.unlink()
    timings = []
    for sequence, frame in enumerate(range(1, 241, 2), start=1):
        timings.append(render_frame(scene, frame, frames / f'frame_{sequence:04d}.png'))
    video, gif = encode(frames)
    (ROOT / 'preview-render-result.json').write_text(json.dumps({
        'source': SOURCE.name,
        'source_sha256': source_sha256,
        'settings': chosen,
        'frame_count': len(timings),
        'render_seconds': sum(timings),
        'video': video.name,
        'gif': gif.name,
    }, indent=2))
    print(f'PREVIEW_DONE {video} {gif}', flush=True)


if __name__ == '__main__':
    main()
