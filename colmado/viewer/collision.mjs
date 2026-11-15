// Static, axis-aligned collision in the horizontal X/Z plane.
// Fixed eye height deliberately avoids gravity, jumping and falling out of the set.
export function createCollisionWorld(data) {
  const radius = data.player?.radius ?? 0.28;
  const eyeHeight = data.player?.height ?? 1.65;
  const bodyTop = eyeHeight + 0.15;
  const bounds = data.bounds;
  if (!bounds || ![bounds.minX, bounds.maxX, bounds.minZ, bounds.maxZ].every(Number.isFinite)) {
    throw new Error('Faltan los límites del recorrido.');
  }
  const boxes = (data.boxes ?? []).filter(box =>
    box.min?.length === 3 && box.max?.length === 3 &&
    box.min[1] < bodyTop && box.max[1] > 0.12
  ).map(box => ({
    name: box.name,
    minX: box.min[0] - radius,
    maxX: box.max[0] + radius,
    minZ: box.min[2] - radius,
    maxZ: box.max[2] + radius,
  }));
  const inset = {
    minX: bounds.minX + radius,
    maxX: bounds.maxX - radius,
    minZ: bounds.minZ + radius,
    maxZ: bounds.maxZ - radius,
  };
  function isFree(x, z) {
    if (x < inset.minX || x > inset.maxX || z < inset.minZ || z > inset.maxZ) return false;
    return !boxes.some(box => x > box.minX && x < box.maxX && z > box.minZ && z < box.maxZ);
  }
  function clampPoint(point) {
    return {
      x: Math.max(inset.minX, Math.min(inset.maxX, point.x)),
      z: Math.max(inset.minZ, Math.min(inset.maxZ, point.z)),
    };
  }
  function move(position, dx, dz) {
    // <= radius/3 per step prevents tunnelling even across very thin walls.
    const distance = Math.hypot(dx, dz);
    if (!Number.isFinite(distance)) return {...position};
    const steps = Math.max(1, Math.ceil(distance / Math.max(0.025, radius / 3)));
    const stepX = dx / steps, stepZ = dz / steps;
    let p = clampPoint(position);
    for (let i = 0; i < steps; i++) {
      const nx = Math.max(inset.minX, Math.min(inset.maxX, p.x + stepX));
      if (isFree(nx, p.z)) p.x = nx;
      const nz = Math.max(inset.minZ, Math.min(inset.maxZ, p.z + stepZ));
      if (isFree(p.x, nz)) p.z = nz;
    }
    return p;
  }
  function safeSpawn(spawn) {
    const preferred = clampPoint({x: spawn?.[0] ?? 0, z: spawn?.[2] ?? -3});
    if (isFree(preferred.x, preferred.z)) return preferred;
    for (let r = 0.5; r <= 12; r += 0.5) {
      for (let i = 0; i < 32; i++) {
        const angle = i * Math.PI * 2 / 32;
        const p = {x: preferred.x + Math.cos(angle) * r, z: preferred.z + Math.sin(angle) * r};
        if (isFree(p.x, p.z)) return p;
      }
    }
    throw new Error('No hay un punto de inicio libre en el recorrido.');
  }
  return {move, isFree, safeSpawn, eyeHeight, radius, bounds: inset, boxCount: boxes.length};
}
