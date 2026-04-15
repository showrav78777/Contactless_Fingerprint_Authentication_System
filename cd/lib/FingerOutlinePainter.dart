import 'package:flutter/material.dart';

class FingerOutlinePainter extends CustomPainter {
  final String fingerType;

  FingerOutlinePainter(this.fingerType);

  @override
  void paint(Canvas canvas, Size size) {
    // Create a Paint object for the finger outlines
    final Paint outlinePaint = Paint()
      ..color = Colors.white.withOpacity(0.8) // White outline for better visibility
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;

    // Create a Paint object for the blur effect
    final Paint blurPaint = Paint()
      ..color = Colors.black.withOpacity(0.7) // Darker blur for better contrast
      ..style = PaintingStyle.fill;

    Path path = Path();

    if (fingerType == 'left thumb') {
// Left thumb outline with rounded upper and open lower
// Right Thumb Outline
// Centered Right Thumb Outline
      double thumbWidth = size.width * 0.4; // Width of the thumb
// Height of the thumb

      path.moveTo(size.width * 0.5 - thumbWidth / 2,
          size.height * 0.75); // Start point at the base of the thumb
      path.lineTo(size.width * 0.5 - thumbWidth / 2,
          size.height * 0.4); // Straight up for the left side
      path.quadraticBezierTo(
          size.width * 0.5,
          size.height * 0.3, // Curve to the right for the rounded upper part
          size.width * 0.5 + thumbWidth / 2,
          size.height * 0.4 // Top curve
          );
      path.lineTo(size.width * 0.5 + thumbWidth / 2,
          size.height * 0.75); // Straight down for the right side
      path.close(); // Close the path to complete the thumb shape
    } else if (fingerType == '4 left fingers') {
// Left-Hand: Index Finger
      {
        double yOffset = size.height * 0.21; // Center position for index finger
        double fingerWidth = size.width * 0.18; // Width of the index finger

        path.moveTo(
            size.width - (size.width * 34 + fingerWidth + size.width * 10),
            yOffset + fingerWidth); // Start at the bottom (mirrored)
        path.lineTo(size.width - (size.width * 2),
            yOffset - fingerWidth); // Straight up for the index finger
        path.quadraticBezierTo(
            size.width - (size.width * 0.4),
            yOffset -
                fingerWidth -
                (fingerWidth * 0.4), // Curve to the left (mirrored)
            size.width - (size.width * 0.2),
            yOffset // Top curve
            );
        path.lineTo(size.width - (size.width * 0.2),
            yOffset + fingerWidth * 0.9); // Right side
        path.quadraticBezierTo(
            size.width - (size.width * 0.4),
            yOffset + fingerWidth + (fingerWidth * 0.2), // Back curve down
            size.width - (size.width * 0.7),
            yOffset + fingerWidth // Back to start
            );
      }

// Left-Hand: Middle Finger
      {
        double yOffset =
            size.height * 0.4; // Center position for middle finger
        double fingerWidth = size.width * 0.18; // Width of the middle finger

        path.moveTo(
            size.width - (size.width * 28 + fingerWidth + size.width * 0.4),
            yOffset + fingerWidth); // Start at the bottom (mirrored)
        path.lineTo(size.width - (size.width * 4),
            yOffset - fingerWidth); // Straight up for the middle finger
        path.quadraticBezierTo(
            size.width - (size.width * 0.4),
            yOffset -
                fingerWidth -
                (fingerWidth * 0.3), // Curve to the left (mirrored)
            size.width - (size.width * 0.05),
            yOffset // Top curve
            );
        path.lineTo(size.width - (size.width * 0.05),
            yOffset + fingerWidth * 0.8); // Right side
        path.quadraticBezierTo(
            size.width - (size.width * 0.3),
            yOffset + fingerWidth + (fingerWidth * 0.6), // Back curve down
            size.width - (size.width * .9),
            yOffset + fingerWidth // Back to start
            );
      }

// Left-Hand: Ring Finger
      {
        double yOffset = size.height * 0.62; // Center position for index finger
        double fingerWidth = size.width * 0.18; // Width of the index finger

        path.moveTo(
            size.width - (size.width * 34 + fingerWidth + size.width * 10),
            yOffset + fingerWidth); // Start at the bottom (mirrored)
        path.lineTo(size.width - (size.width * 2),
            yOffset - fingerWidth); // Straight up for the index finger
        path.quadraticBezierTo(
            size.width - (size.width * 0.4),
            yOffset -
                fingerWidth -
                (fingerWidth * 0.35), // Curve to the left (mirrored)
            size.width - (size.width * 0.2),
            yOffset // Top curve
            );
        path.lineTo(size.width - (size.width * 0.2),
            yOffset + fingerWidth * 0.8); // Right side
        path.quadraticBezierTo(
            size.width - (size.width * 0.4),
            yOffset + fingerWidth + (fingerWidth * 0.2), // Back curve down
            size.width - (size.width * 0.7),
            yOffset + fingerWidth // Back to start
            );
      }

// Left-Hand: Pinky Finger
      {
        double yOffset = size.height * 0.84; // Center position for pinky finger
        double fingerWidth = size.width * 0.175; // Width of the pinky finger

        path.moveTo(
            size.width - (size.width * 34 + fingerWidth + size.width * 10),
            yOffset + fingerWidth); // Start at the bottom (mirrored)
        path.lineTo(size.width - (size.width * 2),
            yOffset - fingerWidth); // Straight up for the pinky finger
        path.quadraticBezierTo(
            size.width - (size.width * 0.4),
            yOffset -
                fingerWidth -
                (fingerWidth * 0.5), // Curve to the left (mirrored)
            size.width - (size.width * 0.5),
            yOffset // Top curve
            );
        path.lineTo(size.width - (size.width * 0.5),
            yOffset + fingerWidth * 0.42); // Right side
        path.quadraticBezierTo(
            size.width - (size.width * 0.65),
            yOffset + fingerWidth + (fingerWidth * 0.05), // Back curve down
            size.width - (size.width * 0.999),
            yOffset + fingerWidth // Back to start
            );
      }
    } else if (fingerType == 'right thumb') {
// Right thumb outline with rounded upper and open lower
// Centered Right Thumb Outline
      double thumbWidth = size.width * 0.4; // Width of the thumb
// Height of the thumb

      path.moveTo(size.width * 0.5 - thumbWidth / 2,
          size.height * 0.75); // Start point at the base of the thumb
      path.lineTo(size.width * 0.5 - thumbWidth / 2,
          size.height * 0.4); // Straight up for the left side
      path.quadraticBezierTo(
          size.width * 0.5,
          size.height * 0.3, // Curve to the right for the rounded upper part
          size.width * 0.5 + thumbWidth / 2,
          size.height * 0.4 // Top curve
          );
      path.lineTo(size.width * 0.5 + thumbWidth / 2,
          size.height * 0.75); // Straight down for the right side
      path.close(); // Close the path to complete the thumb shape
    } else if (fingerType == '4 right fingers') {
      {
        double yOffset = size.height * 0.18; // Center position for index finger
        double fingerWidth = size.width * 0.2; // Width of the index finger

        path.moveTo(size.width * 34 + fingerWidth + size.width * 10,
            yOffset + fingerWidth); // Start at the bottom
        path.lineTo(size.width * 2,
            yOffset - fingerWidth); // Straight up for the index finger
        path.quadraticBezierTo(
            size.width * 0.45,
            yOffset - fingerWidth - (fingerWidth * 0.35), // Curve to the left
            size.width * 0.2,
            yOffset // Top curve
            );
        path.lineTo(
            size.width * 0.2, yOffset + fingerWidth * 0.8); // Right side
        path.quadraticBezierTo(
            size.width * 0.6,
            yOffset + fingerWidth + (fingerWidth * 0.1), // Back curve down
            size.width * 0.8,
            yOffset + fingerWidth // Back to start
            );
      }

// Middle Finger
      {
        double yOffset =
            size.height * 0.41; // Center position for middle finger
        double fingerWidth = size.width * 0.2; // Width of the middle finger

        path.moveTo(size.width * 26 + fingerWidth + size.width * 0.4,
            yOffset + fingerWidth); // Start at the bottom
        path.lineTo(size.width * 3.2,
            yOffset - fingerWidth); // Straight up for the middle finger
        path.quadraticBezierTo(
            size.width * 0.3,
            yOffset - fingerWidth - (fingerWidth * 0.35), // Curve to the left
            size.width * 0.1,
            yOffset // Top curve
            );
        path.lineTo(
            size.width * 0.1, yOffset + fingerWidth * 0.2); // Right side
        path.quadraticBezierTo(
            size.width * 0.2,
            yOffset + fingerWidth + (fingerWidth * 0.6), // Back curve down
            size.width * .8,
            yOffset + fingerWidth // Back to start
            );
      }

// Ring Finger
      {
        double yOffset = size.height * 0.65; // Center position for index finger
        double fingerWidth = size.width * 0.2; // Width of the index finger

        path.moveTo(size.width * 34 + fingerWidth + size.width * 10,
            yOffset + fingerWidth); // Start at the bottom
        path.lineTo(size.width * 2,
            yOffset - fingerWidth); // Straight up for the index finger
        path.quadraticBezierTo(
            size.width * 0.45,
            yOffset - fingerWidth - (fingerWidth * 0.35), // Curve to the left
            size.width * 0.2,
            yOffset // Top curve
            );
        path.lineTo(
            size.width * 0.2, yOffset + fingerWidth * 0.9); // Right side
        path.quadraticBezierTo(
            size.width * 0.6,
            yOffset + fingerWidth + (fingerWidth * 0.15), // Back curve down
            size.width * 0.7,
            yOffset + fingerWidth // Back to start
            );
      }

// Pinky Finger
      {
        double yOffset = size.height * 0.88; // Center position for index finger
        double fingerWidth = size.width * 0.175; // Width of the index finger

        path.moveTo(size.width * 34 + fingerWidth + size.width * 10,
            yOffset + fingerWidth); // Start at the bottom
        path.lineTo(size.width * 2,
            yOffset - fingerWidth); // Straight up for the index finger
        path.quadraticBezierTo(
            size.width * 0.4,
            yOffset - fingerWidth - (fingerWidth * 0.5), // Curve to the left
            size.width * 0.4,
            yOffset // Top curve
            );
        path.lineTo(
            size.width * 0.4, yOffset + fingerWidth * 0.4); // Right side
        path.quadraticBezierTo(
            size.width * 0.65,
            yOffset + fingerWidth + (fingerWidth * 0.05), // Back curve down
            size.width * 0.999,
            yOffset + fingerWidth // Back to start
            );
      }
    }

// Draw the blurred area outside the outline
    final blurPath = Path()
      ..addRect(Rect.fromLTWH(
          0, 0, size.width, size.height)); // Full screen rectangle
    blurPath.fillType =
        PathFillType.evenOdd; // Use even-odd fill rule for the blur effect
    blurPath.addPath(
        path, Offset.zero); // Add the path to the rectangle for exclusion

// Fill the blurred area outside the outlines
    canvas.drawPath(blurPath, blurPaint);

// Draw the finger outlines on top
    canvas.drawPath(path, outlinePaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}
