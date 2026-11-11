// The Land Cruiser's ride and the sand under it: a sprung body on four wheels (heave, pitch and roll), the engine's
// pull limited by the ground's grip, tyres that sink into soft sand, more when they spin (تغريز), and the car's turning
// as a single-track model: each axle's tyres pull sideways by their slip angle, up to what of their grip the drive or
// the brakes leave, so the car understeers when pushed, runs wide under power, tucks in off the pedal, slides on sand
// and, with the stability control off, can be held in a drift or spun. No physics engine: a few dozen multiplications
// per wheel per step, four steps a frame.
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
  driveline: 0.68,         // share of the engine's work reaching the tyres (game choice: 0-100 km/h then about 6.6 s; published about 6.7)
  trcSlip: 0.12,           // traction control (A-TRC, standard): the engine held back so the tyres slip no more than this
  cdA: 1.1,                // drag area, m^2 (game choice: Cd about 0.36 over about 3 m^2)
  vmax: 210 / 3.6,         // m/s, governed top speed (about)
  roadKPa: 230, airedKPa: 100,     // tyre pressure: the door placard's (about 2.3 bar), and aired down for sand (15 psi, the custom in the Nafud)
  turnRadius: 5.9,         // m, the least turning radius, at the outer front tyre (Toyota): the front wheels' full lock is the angle that gives it
  gyrYaw: 1.45,            // m, radius of gyration about the vertical (game choice: about half the wheelbase)
  cornerF: 9.0, cornerR: 13.0,     // the axles' cornering stiffness per unit of load, per radian (game choice: all-terrain tyres; the softer front gives an understeer of about 2 degrees per g)
  rearTorque: 0.6,         // of the drive to the rear axle (the centre differential's nominal 40:60; about)
  rollBar: 73e3,           // N m per radian, the anti-roll bars over the springs (game choice: the body leans about 6 degrees per g; on the springs alone it was near 10)
  stopTravel: 0.05,        // m: the bump stop's own travel, to the suspension's hard end (game choice)
  stopBack: 0.35,          // of the bump stop's push given back as it springs out (game choice: rubber loses most of it)
  stopMax: 6,              // of a wheel's static load: the most it carries on its bump stop (game choice)
  antiDive: 0.6,           // of the pitching moment reaching the springs (game choice: the suspension's anti-dive and anti-squat geometry; the nose dipped 3.7 degrees in a full stop)
};

// The sand. Soft sand (s = 1) under a tyre at road pressure, rolling slowly: it sinks about SINK0. Sinkage grows with
// the ground pressure as Bekker's law has it for dry sand (z ~ p^(1/n), n = 1.1: Wong, Theory of Ground Vehicles,
// table 2.3); the depth itself is a game choice. Rolling quicker it rides higher (PLANE). Spinning, it digs (DIG
// metres of sinkage per metre of slip); rolling without spinning it climbs back out (CLIMB of the dug depth per metre).
// Resistance: the rut it pushes (f0 on hard ground, plus RUT times the sinkage over the tyre's radius on sand); the
// grip: sand's friction angle (28 degrees, the same table: tan = 0.53) against hard ground's 0.85, a softer tyre a
// little more (a longer patch). Past the clearance the chassis drags on the sand (BELLY of the weight).
// Loose sand also drags on a rolling tyre whatever its sinkage (SAND_F at road pressure, less aired down: Wong gives
// 0.1-0.3 for tyres in loose sand), and a soft tyre on hard ground drags more (f0 times (road/pressure)^0.7). Digging
// starts past DIG_SLIP: traction control holds the slip under it (and so never digs), at the cost of some pull in
// sand (TRC_LOSS of the grip, its braking of the spinning wheels); off, the tyres pull to the full grip and dig when
// pressed past it, the more the slower the car goes (none past DIG_V: at speed a spinning tyre throws the sand back and
// rides on: with a run-up, traction control off keeps the momentum that it would cut; from a standstill, a foot held
// down with it off digs in). Backing out along the hole (the other way from the digging) meets BACK_OUT of its drag
// (the tyre climbs the sand it packed) and climbs out twice as fast. Quicker, the tyres throw more sand: SAND_V of
// drag per m/s in soft sand (less aired down). Low range: a key's pedal comes in at half the rate (a finer foot; the touch pedal is the thumb's own), and off
// the pedal the engine holds a descent to a crawl (up to LOW_HOLD of the weight; high range ENGINE_BRAKE). An
// automatic creeps at idle (CREEP of the weight). These shares are game choices.
// Sideways. Game choices, all of them.
const LAT = {
  LO: 1.5, HI: 4.5,         // m/s: under LO the car follows its wheels; over HI the tyres' slip-angle model; blended between
  FOLLOW: 12,               // 1/s: how fast the model's states follow the wheels' path at a crawl
  SLIP_V: 0.1,              // m/s added under a slip angle, so it stays finite at no speed
  FZ_MIN: 0.1,              // the least share of the weight an axle is taken to carry (a hard stop or a hard pull must not leave an axle none)
  FLOOR: 0.12,              // the least share of an axle's grip left sideways whatever the drive or the brakes take (a spinning or locked tyre still pushes a little). With 0.25, and the brakes eased for 0.6 of the grip, the hard-braked front kept more side grip than the lightened rear and the car spun, braking in a turn with the stability control off
  TC_USE: 0.8,              // the most of an axle's grip traction control lets the drive use
  ABS_REAR: 0.75,           // the most of the rear axle's grip its brakes use (the rear is braked gently, as real anti-lock brakes do; a stop from 100 km/h is about 2 m longer for it)
  CIRCLE: 1.03,             // the tyres' whole force, of the car's grip, at most
  BACK_KIN: 6,              // m/s: backing up to this the car follows its wheels (the gearbox backs to 20 km/h)
  ABS_STEER: 0.25, ABS_SIDE: 0.95, ABS_MIN: 0.3,      // braking in a turn: the share of the car's grip the steering may claim, of an axle's own grip that may go sideways, and the least the brakes keep
  SAND_SIDE: 0.55,          // how much softer sideways a tyre is in loose sand
  KIN_GRIP: 0.95,           // of the grip: the tightest turn the wheels' own path takes (at a crawl and backing)
  VSC_BAND: 0.1, VSC_BAND_V: 15,     // rad/s: the yaw-rate error the stability control allows; narrower over VSC_BAND_V m/s, by the speed
  VSC_SLIP: 0.14,           // rad: the rear slip angle it allows
  VSC_GRIP: 0.9,            // of the grip left sideways: the turn it takes the steering to ask for at most
  VSC_GAIN: 9, VSC_GAIN_SLIP: 18,    // 1/s and 1/s per rad: its yaw moment per error
  VSC_BRAKE: 0.5,           // the share of the grip its braking may use, at half the track (with 0.35, one drive in thirty of random hard driving still slid past 30 degrees; with 0.5, one in ninety, all on sand above 130 km/h)
  VSC_CUT: 0.8, VSC_CUT_YAW: 3, VSC_CUT_SLIP: 5, VSC_ON: 20, VSC_OFF: 3,      // the most it cuts the engine, how much per error, and how fast the cut comes and goes (1/s)
  PAD_ASK: 1.0, PAD_MORE: 0.035, PAD_EASE: 2,        // the steering pad: the share of the grip its full travel asks for, the angle added at its end (rad), and how fast it follows a change of ground (1/s)
};
const SAND = { SINK0: 0.07, N: 1.1, PLANE: 25, DIG: 0.05, DIG_SLIP: 0.15, CLIMB: 0.25, F0: 0.015, SAND_F: 0.08, SAND_V: 0.006, DIG_V: 4, RUT: 1.6, MU_HARD: 0.85, MU_SAND: 0.53, MU_AIRED: 0.05,
  BELLY: 0.45, MAXSINK: 0.36, TRC_LOSS: 0.12, ENGINE_BRAKE: 0.03, LOW_HOLD: 0.6, CREEP: 0.07, BACK_OUT: 0.2, MAX_TILT: 0.3, LOAD_EASE: 3, SINK_RATE: 0.4 };

export function createCar(geo, spec = LC300) {
  // geo: { front, rear, half, tyre } from the model's wheels (hub x of the axles, half the track, tyre radius)
  const g = 9.81, m = spec.mass, wb = geo.front - geo.rear;
  const xcg = geo.rear + spec.frontShare * wb;
  const wheels = ['FL', 'FR', 'RL', 'RR'].map((k) => {
    const front = k[0] === 'F', x = front ? geo.front : geo.rear, z = k[1] === 'L' ? -geo.half : geo.half;
    const load = m * g * (front ? spec.frontShare : 1 - spec.frontShare) / 2;      // static, N
    const mq = load / g, w = 2 * Math.PI * spec.rideHz[front ? 0 : 1];
    return { k, front, x, z, load, kS: mq * w * w, cS: 2 * spec.zeta * mq * w, u: 0, uPrev: 0, F: load, Fs: load, sink: 0, dug: 0, digDir: 1, soft: 0, ground: 0, contact: true, spin: 0, slip: 0 };
  });
  const Ip = m * spec.gyrPitch ** 2, Ir = m * spec.gyrRoll ** 2, Iz = m * spec.gyrYaw ** 2, gs = [0, 0, 0, 0];
  const hardEnd = spec.bump + spec.stopTravel;                                // the wheel's travel up at its hard end
  const understeer = 1 / spec.cornerF - 1 / spec.cornerR;                     // rad of steer per g of turn (the softer front)
  const vCh2 = wb * g / understeer;                                           // the characteristic speed, squared
  const s = {
    v: 0, thr: 0, gear: 'D', hillHold: 0, slide: 0, vyL: 0, r: 0, vlat: 0, beta: 0, mu: SAND.MU_HARD, padMu: SAND.MU_HARD, padSoft: 0, vscCut: 0, low: false, trc: true, kPa: spec.roadKPa, yc: 0, vy: 0, pitch: 0, vp: 0, roll: 0, vr: 0, aLong: 0, aLat: 0, yawRate: 0,
    slip: 0, stuck: 0, spinAngle: 0, wheels, xcg, wb,
  };

  // the body's height at a point of the car's frame, from heave at the centre of gravity, pitch and roll (small angles)
  const bodyAt = (x, z) => s.yc + (x - xcg) * s.pitch - z * s.roll;

  function settle(pose, env) {
    const gs = wheels.map((w) => groundAt(pose, w, env));
    s.yc = (gs[0] + gs[1] + gs[2] + gs[3]) / 4 + 0;
    s.pitch = Math.atan2((gs[0] + gs[1]) - (gs[2] + gs[3]), 2 * wb);
    s.roll = Math.atan2((gs[0] + gs[2]) - (gs[1] + gs[3]), 4 * geo.half);
    s.vy = s.vp = s.vr = 0; s.vyL = s.r = s.vlat = s.yawRate = s.vscCut = 0;
    for (let j = 0; j < 4; j++) { const w = wheels[j]; w.u = w.uPrev = 0; w.F = w.Fs = w.load; w.gLast = gs[j]; }
  }

  function groundAt(pose, w, env) {
    const c = Math.cos(pose.yaw), sn = Math.sin(pose.yaw);
    // car frame (x forward, z right) to the world: forward is (cos yaw, -sin yaw), right is (sin yaw, cos yaw)
    const X = pose.x + c * w.x + sn * w.z, Z = pose.z - sn * w.x + c * w.z;
    w.wx = X; w.wz = Z; w.soft = env.soft ? env.soft(X, Z) : 0;
    return env.height(X, Z);
  }

  // ctl: { gas 0..1, brake 0..1, analog } as the pedals are pressed (s.gear 'D' or 'R' says which way gas drives); steer (rad, + to the left); pose { x, z, yaw }: where the
  // car stands (moved by the caller along its heading by s.v). env: { height(x, z), soft(x, z) 0..1 }.
  function step(dt, ctl, steer, pose, env) {
    if (!(dt > 0)) return s;                                                  // (a zero frame from a coarse timer would make 0/0)
    const vStart = s.v;
    const n = 4, h = dt / n;
    // the pedal: how far it is pressed, 0 to 1. From a key (on or off) it is pressed in over about 0.7 s, so that a
    // tap is a gentle pull (a key is not a foot); from the touch pedal (ctl.analog) the thumb is the foot, and the
    // engine answers it in about 0.2 s
    const want = Math.min(1, Math.max(0, +ctl.gas || 0)), bk = Math.min(1, Math.max(0, +ctl.brake || 0));
    s.thr += (want - s.thr) * Math.min(1, dt * (want > s.thr ? (ctl.analog ? 5 : s.low ? 0.7 : 1.4) : 6));
    for (let j = 0; j < 4; j++) { gs[j] = groundAt(pose, wheels[j], env); if (wheels[j].gLast === undefined) wheels[j].gLast = gs[j]; }       // (one array for the car's life: no garbage each frame)
    // the tyres in the sand: how deep each sits, how much it resists and grips
    const press = Math.pow(s.kPa / spec.roadKPa, 1 / SAND.N);
    // Resistance and grip come from each wheel's share of the car's weight on the ground (the springs' static loads,
    // shifted only by how much of the car is on the ground): taking the springs' instant forces, a bounce inflated the
    // grip, the grip the turn, the turn the roll, and the roll the bounce (the car leapt into the air in a turn).
    let res = 0, muSum = 0, sumF = 0, slipV = 0, touching = 0;
    for (const w of wheels) {
      // (the load it sinks by is the spring's force eased over about a third of a second, within a half to twice
      // the static load, and the depth itself moves no faster than SINK_RATE: by the spring's force of the instant, a
      // bounce on a hump flipped the depth 5, 25, 0 cm from frame to frame into the bump stop and threw the car 30 m up)
      w.Fs += (Math.max(0.5 * w.load, Math.min(2 * w.load, w.F)) - w.Fs) * Math.min(1, dt * SAND.LOAD_EASE);
      const loadK = Math.pow(w.Fs / w.load, 1 / SAND.N);
      const lying = SAND.SINK0 * w.soft * press * loadK / (1 + Math.abs(s.v) / SAND.PLANE);
      // the dug hole: driving back out along it (the other way from the digging) the tyre climbs the sand it packed
      const going = Math.abs(s.v) > 0.05 ? Math.sign(s.v) : (s.gear === 'R' ? -1 : 1);         // (standing: the way the gear would take it)
      const hole = w.dug * (going * w.digDir < 0 ? SAND.BACK_OUT : 1);
      const sinkTo = Math.min(SAND.MAXSINK, lying + w.dug); w.sink += Math.max(-SAND.SINK_RATE * dt, Math.min(SAND.SINK_RATE * dt, sinkTo - w.sink));
      const f = SAND.F0 * Math.pow(spec.roadKPa / s.kPa, 0.7) + w.soft * ((SAND.SAND_F + SAND.SAND_V * Math.abs(s.v)) * press + SAND.RUT * (lying + hole) / geo.tyre);
      const deep = lying + hole, belly = deep > spec.clearance * 0.85 ? SAND.BELLY * Math.min(1, (deep - spec.clearance * 0.85) / 0.06) : 0;
      const on = w.contact ? 1 : 0; touching += on * 0.25;
      res += on * w.load * (f + belly);
      w.mu = SAND.MU_HARD + (SAND.MU_SAND - SAND.MU_HARD) * w.soft + (s.kPa < spec.roadKPa ? SAND.MU_AIRED * w.soft * (spec.roadKPa - s.kPa) / (spec.roadKPa - spec.airedKPa) : 0);
      muSum += on * w.load * w.mu;
      sumF += on * w.load;
    }
    const grip = muSum;                                                       // N: the tyres' friction times their static loads on the ground
    // the engine through the gearbox: torque-limited low down, power-limited above (4x4: all four wheels pull)
    const gear = spec.first * spec.final * (s.low ? spec.low : 1);
    const vTop = s.low ? 45 / 3.6 : spec.vmax;
    const dir = s.gear === 'R' ? -1 : 1;
    const rise = (gs[0] + gs[1] - gs[2] - gs[3]) / 2, slope = rise / Math.hypot(wb, rise);      // the ground's slope under the wheels (not the body's pitch on its springs)
    // an automatic in gear creeps at idle (CREEP of the weight, falling off by 2 m/s: about 5 km/h on the flat);
    // hill-start assist (standard on the LC300; on a slope only) holds the brakes after they are let off at a stop,
    // until the engine pulls harder than the slope, or 2 s
    if (ctl.brake && Math.abs(s.v) < 0.3 && slope * dir > 0.03) s.hillHold = 2; else if (s.hillHold > 0) s.hillHold -= dt;      // (facing uphill in the gear's way only: it stops a roll back)
    const creep = s.thr < 0.05 ? m * g * SAND.CREEP * Math.max(0, 1 - Math.abs(s.v) / 2.0) : 0;
    const softAvg = (wheels[0].soft + wheels[1].soft + wheels[2].soft + wheels[3].soft) / 4;
    const vCap = dir < 0 ? 20 / 3.6 : vTop;                                   // reverse: the gearbox's one reverse gear, governed here
    const governor = Math.max(0, Math.min(1, (vCap - Math.abs(s.v)) / 1.0));  // (eased over the last 1 m/s: an on-off cut made the body nod)
    const engine = s.thr * Math.min(spec.torque * gear * spec.driveline / geo.tyre, spec.power * spec.driveline / Math.max(1.5, Math.abs(s.v))) * governor;
    const pull = (s.trc ? Math.min(engine + creep, grip * (1 + spec.trcSlip)) : engine + creep) * (1 - s.vscCut);       // traction control cuts the engine at the grip; the stability control cuts it in a slide
    let drive = Math.min(pull, grip * (s.trc ? 1 - SAND.TRC_LOSS * softAvg : 1));
    s.slip = pull > grip && pull > 1 ? (pull - grip) / pull : 0;
    slipV = Math.max(0, s.slip - SAND.DIG_SLIP) * Math.max(2, Math.abs(s.v) + 6) * s.thr;     // how fast the tyres' faces slide over the sand past what traction holds
    // brakes (all four, to the grip), engine braking off the pedal (low range holds a descent to a crawl), the ruts,
    // the air and the slope
    const air = 0.5 * 1.2 * spec.cdA * s.v * s.v;
    const downhill = -m * g * slope * Math.sign(s.v || dir);
    const holding = ctl.brake || (s.hillHold > 0 && drive < Math.abs(m * g * slope) + 50);
    const engineBrake = s.thr < 0.05 && Math.abs(s.v) > 2.0 ? m * g * (s.low ? Math.min(SAND.LOW_HOLD, 0.05 + 0.25 * (Math.abs(s.v) - 2.0)) : SAND.ENGINE_BRAKE) : 0;
    const brake = Math.min(grip, (holding ? m * g * 0.9 * (bk || 1) : 0) + engineBrake);      // (the brake pedal by how far it is pressed, on top of the engine's braking: a light foot replaced low range's hold on a descent and the car ran away; hill hold, full)
    let F = (holding && !ctl.gas ? 0 : dir * drive) - m * g * slope;
    if (ctl.brake && ctl.gas) F = dir * drive - m * g * slope;              // both feet: the engine pulls against the brakes, each by how far it is pressed
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
    s.v = Math.min(spec.vmax, s.v);
    // Turning: a single-track model about the centre of gravity (lateral speed and yaw rate; + to the left, as the
    // steer). Each axle's tyres pull sideways by their slip angle (stiffness times the angle, bending over to the
    // grip: tanh), on what the friction circle leaves of the axle's grip after the drive and the brakes; the axles'
    // loads shift with the car's acceleration.
    // - The drive goes 40:60 front to rear while both axles hold it; what an axle cannot hold goes to the other (the
    //   centre differential), so with every wheel spinning both ends lose their side grip together.
    // - The brakes are shared by the axles' loads (electronic brake distribution: with a fixed share the lightened
    //   rear locked first and the car spun, braking in a turn), and the anti-lock brakes ease them to leave the tyres
    //   the side force the steering asks for (up to ABS_STEER of the grip; never below ABS_MIN of an axle's own).
    // - Traction control keeps the tyres from using more than TC_USE of their grip along the car, so it still steers;
    //   off, a foot held down takes the rear's grip first and the tail swings out.
    // - On sand the tyres are softer sideways (SAND_SIDE).
    // - At a crawl (under LO, blended up to HI, by the car's whole speed: a car sliding sideways stays with the
    //   tyres' model), and backing, the car follows its wheels, within the grip (no slip angle is defined at a standstill).
    const a = geo.front - xcg, b = xcg - geo.rear, vx = s.v, muAvg = sumF > 0 ? grip / sumF : s.mu;      // (off the ground: the grip it last had)
    const tyreDrive = (holding && !ctl.gas) || (ctl.brake && ctl.gas && Math.abs(s.v) < 0.05) ? 0 : Math.abs(drive), tyreBrake = Math.abs(s.v) > 0.05 ? Math.min(grip, brake) : 0;
    const shift = m * s.aLong * spec.cgHeight / wb;                           // load from the front axle to the rear, speeding up
    const FzF = Math.max(LAT.FZ_MIN * m * g, m * g * spec.frontShare - shift) * touching, FzR = Math.max(LAT.FZ_MIN * m * g, m * g * (1 - spec.frontShare) + shift) * touching;
    const muF = (wheels[0].mu + wheels[1].mu) / 2, muR = (wheels[2].mu + wheels[3].mu) / 2, softF = (wheels[0].soft + wheels[1].soft) / 2, softR = (wheels[2].soft + wheels[3].soft) / 2;
    const capF = muF * FzF, capR = muR * FzR, aided = s.trc ? LAT.TC_USE : 1;
    const driveR0 = Math.min(spec.rearTorque * tyreDrive, aided * capR), driveF = Math.min(tyreDrive - driveR0, aided * capF), driveR = Math.min(tyreDrive - driveF, aided * capR);
    const brakeF = FzF / Math.max(1, FzF + FzR);                              // the front axle's share of the braking: its share of the load
    const ask = Math.min(LAT.ABS_STEER * grip, m * Math.abs(vx * vx * Math.tan(steer) / wb));      // the side force the steering asks for
    const leftF = Math.sqrt(Math.max(0, capF * capF - Math.min(ask * b / wb, LAT.ABS_SIDE * capF) ** 2)), leftR = Math.sqrt(Math.max(0, capR * capR - Math.min(ask * a / wb, LAT.ABS_SIDE * capR) ** 2));
    const brF = Math.min(brakeF * tyreBrake, Math.max(LAT.ABS_MIN * capF, leftF)), brR = Math.min((1 - brakeF) * tyreBrake, LAT.ABS_REAR * capR, Math.max(LAT.ABS_MIN * capR, leftR));      // (the rear held under ABS_REAR of its grip: it keeps side grip when the front has none, so a hard stop pushes straight on and does not spin)
    const eased = Math.max(0, tyreBrake - brF - brR);                         // (none in a straight line: there each axle brakes to its own grip)
    const useF = driveF + brF, useR = driveR + brR;
    const spare = (Math.max(0, leftF - useF) + Math.max(0, leftR - useR)) / m;      // what the tyres have left along the car beside the turn's need, for the stability control's braking
    const DF = Math.max(LAT.FLOOR * capF, Math.sqrt(Math.max(0, capF * capF - useF * useF))), DR = Math.max(LAT.FLOOR * capR, Math.sqrt(Math.max(0, capR * capR - useR * useR)));
    const CF = spec.cornerF * FzF * (1 - LAT.SAND_SIDE * softF), CR = spec.cornerR * FzR * (1 - LAT.SAND_SIDE * softR);
    const rGrip = LAT.KIN_GRIP * muAvg * g / Math.max(1, Math.abs(vx)) /* (under 1 m/s the wheels' own turn is always within it) */, rK = Math.max(-rGrip, Math.min(rGrip, vx * Math.tan(steer) / wb)), vyK = b * rK;      // the wheels' own path (the rear axle does not slip), no tighter than the grip turns the car
    const whole = Math.hypot(vx > 0 ? vx : Math.min(0, vx + LAT.BACK_KIN), s.vyL);      // (backing up to BACK_KIN, the wheels' path: only a slide, or going backward faster than a gearbox backs, brings the tyres' model in)
    const k = whole > LAT.LO ? Math.min(1, (whole - LAT.LO) / (LAT.HI - LAT.LO)) : 0, kk = k * k * (3 - 2 * k), cs = Math.cos(steer), sn = Math.sin(steer);
    let ay = 0, cut = 0, spun = 0;
    if (kk > 0 && eased > 0) s.v += Math.sign(s.v) * eased / m * kk * dt;         // (the braking the anti-lock brakes eased off in the turn)
    for (let i = 0; i < n; i++) {
      if (kk > 0) {
        // each axle's slip angle: between the way its wheels point and the way they go over the ground, rolling
        // forward or back (at no forward speed, a wheel sliding sideways: a right angle); SLIP_V keeps it finite
        const vF = s.vyL + a * s.r, vR = s.vyL - b * s.r;
        const aF = -Math.atan2(vF * cs - vx * sn, Math.abs(vx * cs + vF * sn) + LAT.SLIP_V), aR = -Math.atan2(vR, Math.abs(vx) + LAT.SLIP_V);
        let FyF = DF > 1 ? DF * Math.tanh(CF * aF / DF) : 0, FyR = DR > 1 ? DR * Math.tanh(CR * aR / DR) : 0;      // (no load on an axle, off the ground: no force; 0/0 made the speed NaN for good)
        // stability control (VSC, standard; here it goes off with traction control: a game choice, the real button
        // wants a long press for that): when the yaw rate strays from what the steering asks within the grip, or the
        // rear tyres' slip angle passes VSC_SLIP, the brakes turn the car back and the engine is cut
        let Mv = 0;
        if (s.trc && vx > LAT.LO) {
          // (what the steering asks: the wheels' own path, less this car's understeer, and no more than the grip left
          // after the braking or the pull turns the car. The band it allows narrows with the speed: a yaw rate that
          // is nothing at 40 km/h is a third of a g at 140)
          const latLeft = LAT.VSC_GRIP * Math.sqrt(Math.max(0, (muAvg * g) ** 2 - s.aLong * s.aLong)), lim = latLeft / Math.max(vx, LAT.HI);
          const ref = Math.max(-lim, Math.min(lim, (vx * Math.tan(steer) / wb) / (1 + vx * vx / vCh2))), e = s.r - ref;
          const over = Math.abs(e) - LAT.VSC_BAND * Math.min(1, LAT.VSC_BAND_V / vx), slid = Math.abs(aR) - LAT.VSC_SLIP, mMax = LAT.VSC_BRAKE * grip * geo.half;
          if (over > 0) { Mv = -Math.sign(e) * Math.min(mMax, LAT.VSC_GAIN * over * Iz); cut = Math.max(cut, Math.min(LAT.VSC_CUT, over * LAT.VSC_CUT_YAW)); }
          if (slid > 0 && aR * s.r > 0) { Mv = Math.max(-mMax, Math.min(mMax, Mv - Math.sign(s.r) * LAT.VSC_GAIN_SLIP * slid * Iz)); cut = Math.max(cut, Math.min(LAT.VSC_CUT, slid * LAT.VSC_CUT_SLIP)); }
        }
        // the tyres' whole force held within the car's grip (CIRCLE of it): what the drive, the brakes and the
        // stability control's braking take along the car is taken first, and the side force is cut to what is left
        const vscBrake = Math.min(spare, Math.abs(Mv) / (geo.half * m)), along = driveF + driveR + brF + brR + vscBrake * m, sideAll = Math.abs(FyF * cs + FyR);
        const room = Math.sqrt(Math.max(0, (LAT.CIRCLE * grip * touching) ** 2 - along * along));
        if (sideAll > room) { const q = room / sideAll; FyF *= q; FyR *= q; }
        ay = (FyF * cs + FyR) / m;
        s.vyL += (ay - s.r * vx) * h; s.r += (a * FyF * cs - b * FyR + Mv) / Iz * h;
        // the car's speed along itself: the turned front tyres' drag and the stability control's braking (within what
        // the tyres have left: braking at the limit it moves the brakes from side to side, adding none); and, apart,
        // the share of a slide's speed that the car's turning brings along its own length (no force: kept out of aLong)
        s.v += (-FyF * sn / m - Math.sign(s.v) * vscBrake) * kk * h;
        const turned = s.r * s.vyL * kk * h; s.v += turned; spun += turned;
      }
      if (kk < 1) {                                                         // at a crawl the states follow the wheels, ready for the blend; no faster than the tyres could bring them (the end of a slide was wiped out at 2 g, the yaw rate in one frame)
        const p = (1 - kk) * Math.min(1, h * LAT.FOLLOW), dvMax = muAvg * g * h, drMax = dvMax / b;
        s.r += Math.max(-drMax, Math.min(drMax, (rK - s.r) * p)); s.vyL += Math.max(-dvMax, Math.min(dvMax, (vyK - s.vyL) * p));
      }
    }
    s.vscCut += (cut - s.vscCut) * Math.min(1, dt * (cut > s.vscCut ? LAT.VSC_ON : LAT.VSC_OFF));      // (cut at once, given back over a third of a second)
    s.aLong = (s.v - vStart - spun) / dt;                                     // (with the turn's drag and the eased brakes: the next step's loads and the body's pitch follow what the tyres really did to the car)
    s.yawRate = rK + (s.r - rK) * kk;
    const vyOut = vyK + (s.vyL - vyK) * kk;
    s.vlat = -(vyOut - xcg * s.yawRate);                                      // the model's origin's speed to the car's right (the origin lies xcg behind the centre of gravity): the caller moves the car by it
    s.aLat = kk > 0 ? ay * kk + rK * vx * (1 - kk) : rK * vx;                 // for the body's roll
    s.beta = kk > 0 && vx > LAT.LO ? Math.atan2(-s.vyL + b * s.r, vx) : 0;    // the rear axle's slide (for the dust and the sound)
    if (touching > 0) {                                                       // what the steering pad's travel is measured against: the ground's grip and softness, eased (a jump from hard ground to sand must not jump the wheels)
      const q = Math.min(1, dt * LAT.PAD_EASE); s.mu = muAvg; s.padMu += (muAvg - s.padMu) * q; s.padSoft += ((softF + softR) / 2 - s.padSoft) * q;
    }
    // across a slope steeper than the tyres hold, the car slides down it (s.slide, m/s toward the car's right; the
    // caller moves it): it cannot drive along a 40 degree side slope on two wheels
    const cross = Math.atan2((gs[0] + gs[2]) - (gs[1] + gs[3]), 4 * geo.half);  // + : the left side higher, the slope falls to the right
    const push = g * (Math.abs(Math.sin(cross)) - muAvg * Math.cos(cross) * 0.9);
    s.slide = push > 0 && touching > 0 ? s.slide + Math.sign(cross) * push * dt : s.slide * Math.max(0, 1 - dt * 6);      // (only while the tyres touch: off the ground it is a fall, not a slide)
    s.slide = Math.max(-6, Math.min(6, s.slide));                             // (sliding sideways, the tyres plough: about 20 km/h at most)
    // digging and climbing out, per wheel
    const dist = Math.abs(s.v) * dt;
    for (const w of wheels) {
      w.slip = s.slip;
      const digging = SAND.DIG * w.soft * slipV * Math.max(0, 1 - Math.abs(s.v) / SAND.DIG_V) * dt;
      if (digging > 1e-5) w.digDir = dir;                                     // which way the hole faces
      w.dug += digging - SAND.CLIMB * w.dug * dist * (1 - s.slip) * (s.v * w.digDir < 0 ? 2 : 1);
      w.dug = Math.max(0, Math.min(SAND.MAXSINK, w.dug));
    }
    // stuck: pulling hard and going nowhere
    s.stuck = (s.thr > 0.25 && Math.abs(s.v) < 0.4 && s.slip > 0.05) ? s.stuck + dt : Math.max(0, s.stuck - dt * 2);
    const groundRoll = Math.atan2((gs[0] + gs[2]) - (gs[1] + gs[3]), 4 * geo.half);
    // the springs: four sub-steps of the sprung body over the wheels (the anti-roll bars hold the body toward the ground's own lean)
    // (touching, above: the tyres carry the turn's and the pull's moments, none off the ground)
    for (let i = 0; i < n; i++) {
      let Fy = -m * g, Mp = touching * m * s.aLong * spec.cgHeight * spec.antiDive, Mr = touching * (m * s.aLat * spec.cgHeight - spec.rollBar * (s.roll - groundRoll));
      for (let j = 0; j < 4; j++) {
        const w = wheels[j];
        // where the ground holds the wheel's centre: the ground under it eased in over the sub-steps from where it was
        // a frame ago. (Read once a frame, a slope came to the dampers as a 3 cm step every frame at 50 km/h; their
        // push up was kept and their pull down, which a wheel cannot give, was dropped: the car floated off an 8 degree
        // climb, all four wheels in the air a third of the time.)
        const wheelY = w.gLast + (gs[j] - w.gLast) * (i + 1) / n + geo.tyre - w.sink;
        const hub = bodyAt(w.x, w.z) + geo.tyre;                              // where the body holds it at ride height
        let u = wheelY - hub;                                                 // + : pushed up into the body (bump)
        // The suspension's hard end, STOP_TRAVEL past the bump stop's start: the body cannot come lower on this wheel.
        // It is lifted back to it and loses its speed toward the ground there (a dead blow, nothing sprung back),
        // each through heave, pitch and roll by their inertias. Without it the body sank through the wheel on a hard
        // landing while the stop's force, however capped, pushed all the way in and all the way out: on a row of
        // 1 m waves at 120 km/h every landing threw the car higher, to 9 m, where a free hop off the crest is 0.6 m.
        if (u > hardEnd) {
          const lx = w.x - xcg, inv = 1 / m + lx * lx / Ip + w.z * w.z / Ir, lift = (u - hardEnd) / inv;
          s.yc += lift / m; s.pitch += lift * lx / Ip; s.roll -= lift * w.z / Ir;
          const closing = (gs[j] - w.gLast) / dt - (s.vy + lx * s.vp - w.z * s.vr);      // the ground's rise there, less the body's
          if (closing > 0) { const blow = closing / inv; s.vy += blow / m; s.vp += blow * lx / Ip; s.vr -= blow * w.z / Ir; }
          u = hardEnd;
        }
        w.contact = u > -spec.droop;
        if (!w.contact) u = -spec.droop;                                      // hanging at full droop, off the ground
        const du = (u - w.uPrev) / h; w.uPrev = u; w.u = u;
        let f = w.contact ? w.load + w.kS * u + w.cS * du : 0;
        if (u > spec.bump) { const e = u - spec.bump; f += w.kS * (25 * e + 800 * e * e) * (du < 0 ? spec.stopBack : 1); }      // the bump stop (rubber: stiffening fast, and giving back only a part of what it took: springing back whole, each landing on a row of waves threw the car higher than the last)
        // (a wheel carries at most STOP_MAX of its static load: the stop's square law grew without end on a hard
        // landing, 600 kN on a wheel and the body thrown higher than the hump that sent it up; past that the tyre
        // and the frame give)
        f = Math.max(0, Math.min(spec.stopMax * w.load, f)); w.F = f;
        Fy += f; Mp += f * (w.x - xcg); Mr -= f * w.z;
      }
      s.vy += Fy / m * h; s.vp += Mp / Ip * h; s.vr += Mr / Ir * h;
      s.yc += s.vy * h; s.pitch += s.vp * h; s.roll += s.vr * h;
      // (a guard on the body's lean against the ground under it, not against level: held to level, a steep side slope
      // drove the uphill wheels into their stops and threw the car)
      const gp = Math.atan2(rise, wb), gr = Math.atan2((gs[0] + gs[2]) - (gs[1] + gs[3]), 4 * geo.half);
      if (Math.abs(s.pitch - gp) > SAND.MAX_TILT) { s.pitch = gp + Math.sign(s.pitch - gp) * SAND.MAX_TILT; s.vp = 0; }
      if (Math.abs(s.roll - gr) > SAND.MAX_TILT) { s.roll = gr + Math.sign(s.roll - gr) * SAND.MAX_TILT; s.vr = 0; }
    }
    for (let j = 0; j < 4; j++) wheels[j].gLast = gs[j];
    // the wheels' turning: rolling with the car, faster when they spin in the sand
    s.spinAngle += (s.v + dir * slipV) * dt / geo.tyre;
    return s;
  }

  // where the car's origin sits (its frame's (0, 0, 0)) for the scene
  const originY = () => s.yc - xcg * s.pitch;
  // The steering. Its full lock is the single-track angle whose outer front tyre runs the least turning radius.
  // steerAsk(p, v): the front wheels' angle for a pad (or key) at p of its travel, -1 to 1, at a speed. At a crawl
  // the pad's travel is the whole lock; quicker, its full travel asks no more than takes the car to the tyres' grip
  // there (PAD_ASK of it) with the steer this car's understeer adds (more on sand, where the tyres are softer), and a little past it at the pad's end (PAD_MORE,
  // by the cube: the middle of the pad stays even). A thumb on a pad is not two hands on a wheel: with the whole
  // lock at speed, half the pad was already the tyres' limit. Game choice.
  const lock = Math.atan(wb / (Math.sqrt(spec.turnRadius ** 2 - wb ** 2) - geo.half));
  const steerAsk = (p, v) => {
    const a = LAT.PAD_ASK * s.padMu * g, lin = Math.min(lock, Math.atan(wb * a / Math.max(1, v * v)) + understeer * a / g / (1 - LAT.SAND_SIDE * s.padSoft)), full = Math.min(lock, lin + LAT.PAD_MORE), q = Math.abs(p);
    return Math.sign(p) * (q * lin + q * q * q * (full - lin));
  };
  return { s, step, settle, originY, wheels, SAND, lock, steerAsk };
}

// How soft the ground is (0 hard, 1 loose dune sand), a game choice over the real terrain: the yard and its approach
// beaten hard; elsewhere patches of loose sand over firmer ground, softer on the gentle slopes and westward toward the
// Nafud (the terrain's west); slopes steeper than about 17 degrees are rock. height: the terrain; inYard(x, z): true on beaten ground.
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
    // sand lies soft on the dunes' gentle faces; the steep slopes round here are the hills' rock (Aban), hard
    const rock = Math.max(0, Math.min(1, (slope - 0.3) * 5));
    return Math.max(0, Math.min(1, (0.15 + 0.65 * patch + Math.min(0.35, slope * 2.5) + west) * (1 - rock)));
  };
}
