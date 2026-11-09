// World -> screen projection matching the prototype's camera (fov 40 vertical, lookAt the target, y up).
function makeCam(target, offset, W, H, fov = 40) {
  const eye = [target[0] + offset[0], target[1] + offset[1], target[2] + offset[2]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const norm = (a) => { const l = Math.hypot(...a); return a.map((v) => v / l); };
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const zc = norm(sub(eye, target)), xc = norm(cross([0, 1, 0], zc)), yc = cross(zc, xc);
  const f = 1 / Math.tan((fov * Math.PI) / 360), aspect = W / H;
  return (p) => {
    const d = sub(p, eye);
    const x = dot(d, xc), y = dot(d, yc), z = dot(d, zc);
    const nx = (f / aspect) * x / -z, ny = f * y / -z;
    return [(nx + 1) / 2 * W, (1 - ny) / 2 * H, -z];
  };
}
if (typeof module !== 'undefined') module.exports = { makeCam };
