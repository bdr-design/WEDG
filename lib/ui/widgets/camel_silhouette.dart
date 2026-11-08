import 'package:flutter/material.dart';

/// Side-view camel silhouette, head to the left, drawn in a 400×300 box.
///
/// Stand-in until the real photographs are added under assets/camels/.
/// [calf] draws a smaller, leggier young camel with a low hump.
class CamelSilhouettePainter extends CustomPainter {
  CamelSilhouettePainter({
    required this.coat,
    required this.shade,
    this.calf = false,
    this.male = false,
  });

  final Color coat;
  final Color shade;
  final bool calf;
  final bool male;

  @override
  void paint(Canvas canvas, Size size) {
    const w = 400.0, h = 300.0;
    final scale = (size.width / w < size.height / h)
        ? size.width / w
        : size.height / h;
    canvas.save();
    canvas.translate(
        (size.width - w * scale) / 2, (size.height - h * scale) / 2);
    canvas.scale(scale);

    if (calf) {
      // Young camels: smaller body, long legs relative to body.
      canvas.translate(70, 70);
      canvas.scale(0.68);
    }

    // Ground shadow.
    final shadow = Paint()..color = Colors.black.withValues(alpha: 0.10);
    canvas.drawOval(const Rect.fromLTWH(95, 282, 230, 14), shadow);

    final farSide = Paint()..color = Color.lerp(coat, shade, 0.55)!;
    final body = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color.lerp(coat, Colors.white, 0.10)!, coat, Color.lerp(coat, shade, 0.35)!],
        stops: const [0, 0.55, 1],
      ).createShader(const Rect.fromLTWH(0, 40, 400, 260));

    // Far legs (drawn first, offset, darker).
    canvas.drawPath(_frontLeg(dx: 20), farSide);
    canvas.drawPath(_hindLeg(dx: -16), farSide);

    final humpTop = calf ? 82.0 : (male ? 46.0 : 52.0);
    canvas.drawPath(_body(humpTop), body);

    // Tail.
    final tail = Paint()
      ..color = Color.lerp(coat, shade, 0.5)!
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(
      Path()
        ..moveTo(328, 132)
        ..quadraticBezierTo(342, 160, 336, 196),
      tail,
    );

    // Ear and eye.
    canvas.drawPath(
      Path()
        ..moveTo(80, 64)
        ..lineTo(86, 49)
        ..lineTo(92, 64)
        ..close(),
      Paint()..color = Color.lerp(coat, shade, 0.3)!,
    );
    canvas.drawCircle(const Offset(57, 67), 3.2, Paint()..color = shade);

    canvas.restore();
  }

  Path _body(double humpTop) {
    return Path()
      ..moveTo(330, 126)
      // Rump up to the hump.
      ..cubicTo(318, 96, 286, humpTop + 4, 248, humpTop)
      // Hump down to the withers.
      ..cubicTo(212, humpTop - 2, 192, 86, 166, 106)
      // Neck top line dips, then rises to the poll.
      ..cubicTo(146, 121, 118, 130, 100, 114)
      ..cubicTo(88, 104, 82, 82, 80, 66)
      // Forehead and long muzzle.
      ..cubicTo(72, 56, 56, 54, 44, 58)
      ..cubicTo(32, 61, 24, 64, 21, 72)
      // Drooping lower lip.
      ..cubicTo(17, 81, 24, 89, 35, 88)
      ..cubicTo(47, 88, 58, 86, 66, 90)
      // Throat down to the chest.
      ..cubicTo(78, 112, 96, 148, 118, 166)
      // Near front leg.
      ..cubicTo(126, 176, 128, 196, 127, 226)
      ..lineTo(124, 284)
      ..quadraticBezierTo(112, 288, 112, 292)
      ..lineTo(140, 292)
      ..lineTo(137, 230)
      ..cubicTo(138, 210, 141, 194, 148, 184)
      // Belly.
      ..cubicTo(182, 194, 238, 194, 268, 182)
      // Near hind leg: thigh, hock, cannon.
      ..cubicTo(270, 204, 272, 232, 274, 286)
      ..quadraticBezierTo(262, 288, 262, 292)
      ..lineTo(292, 292)
      ..lineTo(289, 240)
      ..cubicTo(292, 226, 300, 216, 306, 200)
      ..cubicTo(318, 176, 330, 152, 330, 126)
      ..close();
  }

  Path _frontLeg({required double dx}) => Path()
    ..moveTo(128 + dx, 172)
    ..lineTo(127 + dx, 226)
    ..lineTo(124 + dx, 284)
    ..lineTo(112 + dx, 292)
    ..lineTo(140 + dx, 292)
    ..lineTo(137 + dx, 230)
    ..lineTo(150 + dx, 182)
    ..close();

  Path _hindLeg({required double dx}) => Path()
    ..moveTo(268 + dx, 180)
    ..lineTo(274 + dx, 286)
    ..lineTo(262 + dx, 292)
    ..lineTo(292 + dx, 292)
    ..lineTo(289 + dx, 240)
    ..lineTo(306 + dx, 200)
    ..lineTo(300 + dx, 176)
    ..close();

  @override
  bool shouldRepaint(CamelSilhouettePainter old) =>
      old.coat != coat || old.shade != shade || old.calf != calf || old.male != male;
}
