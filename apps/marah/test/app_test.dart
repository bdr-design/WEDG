import 'package:flutter_test/flutter_test.dart';
import 'package:marah/main.dart';

void main() {
  testWidgets('app starts', (tester) async {
    await tester.pumpWidget(const MarahApp());
    expect(find.text('مراح · قيد البناء'), findsOneWidget);
  });
}
