import 'package:flutter/material.dart';

class HandLandmarkPainter extends CustomPainter {
  final List<Map<String, dynamic>> hands;
  final Size? previewSize;
  final RegistrationStep step;
  final double confidenceThreshold;

  static const List<int> fingertipIndices = [4, 8, 12, 16, 20];
  static const List<int> jointIndices = [3, 7, 11, 15, 19];
  static const List<String> fingertipLabels = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'];
  static const List<List<int>> connections = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 5], [5, 6], [6, 7], [7, 8],
    [5, 9], [9, 10], [10, 11], [11, 12],
    [9, 13], [13, 14], [14, 15], [15, 16],
    [13, 17], [17, 18], [18, 19], [19, 20],
    [0, 5], [0, 17], [5, 9], [9, 13], [13, 17],
  ];

  HandLandmarkPainter(this.hands, this.previewSize, this.step, this.confidenceThreshold);

  @override
  void paint(Canvas canvas, Size size) {
    if (previewSize == null) return;
    final scaleX = size.width / previewSize!.width;
    final scaleY = size.height / previewSize!.height;

    final pointPaint = Paint()..style = PaintingStyle.fill..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);
    final wristPaint = Paint()..color = Colors.red..style = PaintingStyle.fill..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);
    final linePaint = Paint()..color = Colors.white..style = PaintingStyle.stroke..strokeWidth = 2;
    final textPainter = TextPainter(textAlign: TextAlign.left, textDirection: TextDirection.ltr);

    for (final hand in hands) {
      final landmarks = (hand['landmarks'] as List).cast<Map<String, double>>();
      final handLabel = (hand['handedness'] ?? 'Hand').toString().toLowerCase() == 'left' ? 'Left' : 'Right';
      final confidence = hand['confidence'] as double;
      if (landmarks.isEmpty || confidence < confidenceThreshold) continue;

      if (landmarks.isNotEmpty && landmarks[0]['x'] != null && landmarks[0]['y'] != null) {
        final wristX = landmarks[0]['x']! * scaleX;
        final wristY = landmarks[0]['y']! * scaleY;
        canvas.drawCircle(Offset(wristX, wristY), 14.0, wristPaint);
        textPainter.text = TextSpan(text: '$handLabel Wrist', style: const TextStyle(color: Colors.red, fontSize: 14));
        textPainter.layout();
        textPainter.paint(canvas, Offset(wristX + 10, wristY - 10));
      }

      final indicesToDraw = step == RegistrationStep.captureLeftThumb || step == RegistrationStep.captureRightThumb
          ? [0] // Thumb tip only
          : step == RegistrationStep.captureLeftFingers || step == RegistrationStep.captureRightFingers
              ? [0, 1, 2, 3, 4] // All 5 fingertips
              : List<int>.generate(landmarks.length, (i) => i);

      for (final idx in indicesToDraw) {
        if (landmarks.length > idx && landmarks[idx]['x'] != null && landmarks[idx]['y'] != null) {
          final x = landmarks[idx]['x']! * scaleX;
          final y = landmarks[idx]['y']! * scaleY;
          final isFingertip = fingertipIndices.contains(idx % 21);

          canvas.drawCircle(Offset(x, y), isFingertip ? 10.0 : 6.0, pointPaint..color = isFingertip ? Colors.blueAccent : Colors.greenAccent);

          if (isFingertip) {
            final labelIndex = fingertipIndices.indexOf(idx % 21);
            final label = '$handLabel ${fingertipLabels[labelIndex]}';
            textPainter.text = TextSpan(text: label, style: const TextStyle(color: Colors.blueAccent, fontSize: 12));
            textPainter.layout();
            textPainter.paint(canvas, Offset(x + 10, y - 10));
          }
        }
      }

      if (step != RegistrationStep.captureLeftThumb && step != RegistrationStep.captureRightThumb && step != RegistrationStep.captureLeftFingers && step != RegistrationStep.captureRightFingers) {
        for (final connection in connections) {
          final startIdx = connection[0];
          final endIdx = connection[1];
          if (landmarks.length > startIdx && landmarks.length > endIdx && landmarks[startIdx]['x'] != null && landmarks[startIdx]['y'] != null &&
              landmarks[endIdx]['x'] != null && landmarks[endIdx]['y'] != null) {
            final startX = landmarks[startIdx]['x']! * scaleX;
            final startY = landmarks[startIdx]['y']! * scaleY;
            final endX = landmarks[endIdx]['x']! * scaleX;
            final endY = landmarks[endIdx]['y']! * scaleY;
            canvas.drawLine(Offset(startX, startY), Offset(endX, endY), linePaint);
          }
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

enum RegistrationStep {
  showLeftHand,
  detectLeftThumb,
  captureLeftThumb,
  detectLeftFingers,
  captureLeftFingers,
  showRightHand,
  detectRightThumb,
  captureRightThumb,
  detectRightFingers,
  captureRightFingers,
  done,
}