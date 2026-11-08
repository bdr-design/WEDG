import 'dart:typed_data';

/// A linear-RGB colour (not sRGB-encoded).
class Rgb {
  const Rgb(this.r, this.g, this.b);
  final double r;
  final double g;
  final double b;
}

/// Clear desert afternoon sky, linear RGB (about sRGB #8AB8EB).
const Rgb kSkyColour = Rgb(0.254, 0.479, 0.831);

/// Ambient sky radiance for the irradiance harmonics, linear RGB, relative.
const Rgb kSkyRadiance = Rgb(0.42, 0.56, 0.80);

/// Light bounced up from the sand, linear RGB, relative.
const Rgb kGroundRadiance = Rgb(0.46, 0.36, 0.25);

/// Filament's 3-band irradiance spherical harmonics (9 × RGB = 27 floats,
/// already convolved and scaled the way `cmgen --sh-shader` writes them) for
/// a sky of radiance [sky] over the upper hemisphere and [ground] below.
///
/// Filament evaluates `sh[0] + sh[1]·n.y + sh[2]·n.z + sh[3]·n.x + …`, so a
/// hemisphere light is exactly `(sky+ground)/2 + (sky−ground)/2 · n.y`:
/// a surface facing up sees the sky, one facing down sees the ground and a
/// wall sees their mean. The higher bands are zero.
Float32List hemisphereHarmonics(Rgb sky, Rgb ground) {
  final sh = Float32List(27);
  sh[0] = (sky.r + ground.r) / 2;
  sh[1] = (sky.g + ground.g) / 2;
  sh[2] = (sky.b + ground.b) / 2;
  sh[3] = (sky.r - ground.r) / 2;
  sh[4] = (sky.g - ground.g) / 2;
  sh[5] = (sky.b - ground.b) / 2;
  return sh;
}

/// Evaluates [sh] (Filament's 3-band layout) for the unit normal (x, y, z).
/// Only used by the tests to check the coefficients.
Rgb evaluateHarmonics(Float32List sh, double x, double y, double z) {
  final basis = [
    1.0,
    y,
    z,
    x,
    y * x,
    y * z,
    3 * z * z - 1,
    z * x,
    x * x - y * y,
  ];
  var r = 0.0, g = 0.0, b = 0.0;
  for (var i = 0; i < 9; i++) {
    r += sh[i * 3] * basis[i];
    g += sh[i * 3 + 1] * basis[i];
    b += sh[i * 3 + 2] * basis[i];
  }
  return Rgb(r, g, b);
}
