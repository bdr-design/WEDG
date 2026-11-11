// The Land Cruiser's ride and the sand under it: a sprung body on four wheels (heave, pitch and roll), the engine's
// pull limited by the ground's grip, and tyres that sink into soft sand, more when they spin (تغريز). No physics
// engine: a few dozen multiplications per wheel per step, four steps a frame.
// Numbers: sourced where marked; the rest are game choices (docs/GDD.md's rule), chosen to feel like the real car.
// Frame: x forward, y up, z to the right (three.js, the model's own); lengths in metres, forces in newtons.

export const LC300 = {
  mass: 2550,              // kg, ZX kerb weight (Toyota's spec sheet, about)
  frontShare: 0.54,        // of the weight on the front axle (game choice: a front-engined body-on-frame 4x4)
  cgHeight: 0.80,          // m above the ground (game choice)
  rideHz: [1.25, 1.35],    // front, rear ride frequency (game choice: a soft body-on-frame SUV)
  zeta: 0.35,              // damping ratio (game choice)
  bump: 0.10, droop: 0.14, // wheel travel up and down from ride height (game choice; the LC300 articulates far)
  gyrPitch: 1.25, gyrRoll: 0.62,   // radii of gyration, m (game choice: about a quarter of the length, a third of the track)
  clearance: 0.225,        // m, least ground clearance (Toyota, about)
  torque: 650,             // N m, the 3.5 V6 twin-turbo (Toyota)
  power: 305e3,            // W, 415 PS (Toyota)
  first: 4.92, final: 3.31, low: 2.62,   // first gear, final drive, the transfer's low range (Aisin 10-speed; about)
  driveline: 0.85,         // share of the engine's work reaching the tyres (game choice)
  cdA: 1.1,                // drag area, m^2 (game choice: Cd about 0.36 over about 3 m^2)
  vmax: 210 / 3.6,         // m/s, governed top speed (about)
  roadKPa: 230, airedKPa: 100,     // tyre pressure: the door placard's (about 2.3 bar), and aired down for sand (15 psi, the custom in the Nafud)
};

// The sand. Soft sand (s = 1) under a tyre at road pressure, rolling slowly: it sinks about SINK0. Sinkage grows with
// the ground pressure as Bekker's law has it for dry sand (z ~ p^(1/n), n = 1.1: Wong, Theory of Ground Vehicles,
// table 2.3); the depth itself is a game choice. Rolling quicker it rides higher (PLANE). Spinning, it digs (DIG
// metres of sinkage per metre of slip); rolling without spinning it climbs back out (CLIMB of the dug depth per metre).
// Resistance: the rut it pushes (f0 on hard ground, plus RUT times the sinkage over the tyre's radius on sand); the
// grip: sand's friction angle (28 degrees, the same table: tan = 0.53) against hard ground's 0.85, a softer tyre a
// little more (a longer patch). Past the clearance the chassis drags on the sand (BELLY of the weight).
const SAND = { SINK0: 0.07, N: 1.1, PLANE: 8, DIG: 0.05, CLIMB: 0.25, F0: 0.015, RUT: 1.6, MU_HARD: 0.85, MU_SAND: 0.53, MU_AIRED: 0.05, BELLY: 0.45, MAXSINK: 0.36 };

export function createCar(geo, spec = LC300) {
  // geo: { front, rear, half, tyre } from the model's wheels (hub x of the axles, half the track, tyre radius)
  const g = 9.81, m = spec.mass, wb = geo.front - geo.rear;
  const xcg = geo.rear + spec.frontShare * wb;
  const wheels = ['FL', 'FR', 'RL', 'RR'].map((k) => {
    const front = k[0] === 'F', x = front ? geo.front : geo.rear, z = k[1] === 'L' ? -geo.half : geo.half;
    const load = m * g * (front ? spec.frontShare : 1 - spec.frontShare) / 2;      // static, N
    const mq = load / g, w = 2 * Math.PI * spec.rideHz[front ? 0 : 1];
    return { k, front, x, z, load, kS: mq * w * w, cS: 2 * spec.zeta * mq * w, u: 0, uPrev: 0, F: load, sink: 0, dug: 0, soft: 0, ground: 0, contact: true, spin: 0, slip: 0 };
  });
  const Ip = m * spec.gyrPitch ** 2, Ir = m * spec.gyrRoll ** 2;
  const s = {
    v: 0, thr: 0, low: false, kPa: spec.roadKPa, yc: 0, vy: 0, pitch: 0, vp: 0, roll: 0, vr: 0, aLong: 0, aLat: 0,
    slip: 0, stuck: 0, spinAngle: 0, wheels, xcg, wb,
  };

  // the body's height at a point of the car's frame, from heave at the centre of gravity, pitch and roll (small angles)
  const bodyAt = (x, z) => s.yc + (x - xcg) * s.pitch - z * s.roll;

  function settle(pose, env) {
    const gs = wheels.map((w) => groundAt(pose, w, env));
    s.yc = (gs[0] + gs[1] + gs[2] + gs[3]) / 4 + 0;
    s.pitch = Math.atan2((gs[0] + gs[1]) - (gs[2] + gs[3]), 2 * wb);
    s.roll = Math.atan2((gs[0] + gs[2]) - (gs[1] + gs[3]), 4 * geo.half);
    s.vy = s.vp = s.vr = 0;
    for (const w of wheels) { w.u = w.uPrev = 0; w.F = w.load; }
  }

  function groundAt(pose, w, env) {
    const c = Math.cos(pose.yaw), sn = Math.sin(pose.yaw);
    // car frame (x forward, z right) to the world: forward is (cos yaw, -sin yaw), right is (sin yaw, cos yaw)
    const X = pose.x + c * w.x + sn * w.z, Z = pose.z - sn * w.x + c * w.z;
    w.wx = X; w.wz = Z; w.soft = env.soft ? env.soft(X, Z) : 0;
    return env.height(X, Z);
  }

  // ctl: { gas 0..1, brake 0..1 } as the pedals are held; steer (rad, + to the left); pose { x, z, yaw }: where the
  // car stands (moved by the caller along its heading by s.v). env: { height(x, z), soft(x, z) 0..1 }.
  function step(dt, ctl, steer, pose, env) {
    const n = 4, h = dt / n;
    // the pedal: pressed in over about 0.7 s, so that a tap is a gentle pull (a binary button is not a foot)
    const want = ctl.gas ? 1 : 0;
    s.thr += (want - s.thr) * Math.min(1, dt * (want > s.thr ? 1.4 : 6));
    const gs = wheels.map((w) => groundAt(pose, w, env));
    // the tyres in the sand: how deep each sits, how much it resists and grips
    const press = Math.pow(s.kPa / spec.roadKPa, 1 / SAND.N);
    let res = 0, grip = 0, slipV = 0;
    for (const w of wheels) {
      const loadK = Math.pow(Math.max(0, w.F) / w.load, 1 / SAND.N);
      const lying = SAND.SINK0 * w.soft * press * loadK / (1 + Math.abs(s.v) / SAND.PLANE);
      w.sink = Math.min(SAND.MAXSINK, lying + w.dug);
      const f = SAND.F0 + SAND.RUT * w.soft * w.sink / geo.tyre;
      const belly = w.sink > spec.clearance * 0.85 ? SAND.BELLY * Math.min(1, (w.sink - spec.clearance * 0.85) / 0.06) : 0;
      res += Math.max(0, w.F) * (f + belly);
      grip += Math.max(0, w.F) * (SAND.MU_HARD + (SAND.MU_SAND - SAND.MU_HARD) * w.soft + (s.kPa < spec.roadKPa ? SAND.MU_AIRED * w.soft * (spec.roadKPa - s.kPa) / (spec.roadKPa - spec.airedKPa) : 0));
    }
    // the engine through the gearbox: torque-limited low down, power-limited above (4x4: all four wheels pull)
    const gear = spec.first * spec.final * (s.low ? spec.low : 1);
    const vTop = s.low ? 45 / 3.6 : spec.vmax;
    const dir = ctl.reverse ? -1 : 1;
    const engine = s.thr * Math.min(spec.torque * gear * spec.driveline / geo.tyre, spec.power * spec.driveline / Math.max(1.5, Math.abs(s.v))) * (Math.abs(s.v) < vTop ? 1 : 0);
    const drive = Math.min(engine, grip);
    s.slip = engine > grip && engine > 1 ? (engine - grip) / engine : 0;
    slipV = s.slip * Math.max(2, Math.abs(s.v) + 6) * s.thr;                     // how fast the tyres' faces slide over the sand
    // brakes (all four, to the grip), the ruts, the air and the slope
    const slope = Math.sin(s.pitch);
    const air = 0.5 * 1.2 * spec.cdA * s.v * s.v;
    const brake = ctl.brake ? Math.min(grip, m * g * 0.9) : 0;
    let F = dir * drive - m * g * slope;
    const oppose = res + air + brake;
    // resistance and brakes oppose the motion, and when the car stands they hold it unless the push beats them
    if (Math.abs(s.v) < 0.05 && Math.abs(F) <= oppose) { s.v = 0; s.aLong = 0; }
    else {
      const sv = Math.abs(s.v) >= 0.05 ? Math.sign(s.v) : Math.sign(F);
      const a = (F - sv * oppose) / m;
      const v0 = s.v; s.v += a * dt;
      if (Math.sign(s.v) !== Math.sign(v0) && v0 !== 0 && Math.abs(F) <= oppose) s.v = 0;       // stopped, not reversed, by the resistance
      s.aLong = (s.v - v0) / dt;
    }
    s.v = Math.max(-20 / 3.6, Math.min(spec.vmax, s.v));
    s.aLat = s.v * s.v * Math.tan(steer) / wb;
    // digging and climbing out, per wheel
    const dist = Math.abs(s.v) * dt;
    for (const w of wheels) {
      w.slip = s.slip;
      w.dug += SAND.DIG * w.soft * slipV * dt - SAND.CLIMB * w.dug * dist * (1 - s.slip);
      w.dug = Math.max(0, Math.min(SAND.MAXSINK, w.dug));
    }
    // stuck: pulling hard and going nowhere
    s.stuck = (s.thr > 0.6 && Math.abs(s.v) < 0.4 && s.slip > 0.3) ? s.stuck + dt : Math.max(0, s.stuck - dt * 2);
    // the springs: four sub-steps of the sprung body over the wheels
    for (let i = 0; i < n; i++) {
      let Fy = -m * g, Mp = m * s.aLong * spec.cgHeight, Mr = m * s.aLat * spec.cgHeight;
      for (let j = 0; j < 4; j++) {
        const w = wheels[j];
        const wheelY = gs[j] + geo.tyre - w.sink;                               // where the ground holds the wheel's centre
        const hub = bodyAt(w.x, w.z) + geo.tyre;                              // where the body holds it at ride height
        let u = wheelY - hub;                                                 // + : pushed up into the body (bump)
        w.contact = u > -spec.droop;
        if (!w.contact) u = -spec.droop;                                      // hanging at full droop, off the ground
        const du = (u - w.uPrev) / h; w.uPrev = u; w.u = u;
        let f = w.contact ? w.load + w.kS * u + w.cS * du : 0;
        if (u > spec.bump) f += w.kS * 8 * (u - spec.bump);                  // the bump stop
        f = Math.max(0, f); w.F = f;
        Fy += f; Mp += f * (w.x - xcg); Mr -= f * w.z;
      }
      s.vy += Fy / m * h; s.vp += Mp / Ip * h; s.vr += Mr / Ir * h;
      s.yc += s.vy * h; s.pitch += s.vp * h; s.roll += s.vr * h;
    }
    // the wheels' turning: rolling with the car, faster when they spin in the sand
    s.spinAngle += (s.v + dir * slipV) * dt / geo.tyre;
    return s;
  }

  // where the car's origin sits (its frame's (0, 0, 0)) for the scene
  const originY = () => s.yc - xcg * s.pitch;
  return { s, step, settle, originY, wheels, SAND };
}

// How soft the ground is (0 hard, 1 loose dune sand), a game choice over the real terrain: the yard and its approach
// beaten hard; elsewhere patches of loose sand over firmer ground, softer on the dunes' slopes and westward toward the
// Nafud (the terrain's west). height: the terrain; inYard(x, z): true on beaten ground.
export function makeSoftness(height, inYard, westEdge = -35000) {
  const hash = (i, j) => { const t = Math.sin(i * 127.1 + j * 311.7) * 43758.5453; return t - Math.floor(t); };
  const noise = (x, z) => {
    const i = Math.floor(x), j = Math.floor(z), fx = x - i, fz = z - j, sx = fx * fx * (3 - 2 * fx), sz = fz * fz * (3 - 2 * fz);
    const a = hash(i, j), b = hash(i + 1, j), c = hash(i, j + 1), d = hash(i + 1, j + 1);
    return (a * (1 - sx) + b * sx) * (1 - sz) + (c * (1 - sx) + d * sx) * sz;
  };
  return (x, z) => {
    if (inYard(x, z)) return 0.08;
    const e = 2, dx = (height(x + e, z) - height(x - e, z)) / (2 * e), dz = (height(x, z + e) - height(x, z - e)) / (2 * e);
    const slope = Math.hypot(dx, dz);
    const patch = 0.6 * noise(x / 45, z / 45) + 0.4 * noise(x / 11 + 7.3, z / 11 - 2.1);
    const west = Math.min(0.3, Math.max(0, -x / Math.abs(westEdge)) * 0.6);
    return Math.max(0, Math.min(1, 0.15 + 0.65 * patch + Math.min(0.35, slope * 2.5) + west));
  };
}
