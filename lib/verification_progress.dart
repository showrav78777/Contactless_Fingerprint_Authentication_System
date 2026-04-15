import 'package:flutter/material.dart';
import 'dart:math' as math;

class VerificationProgress extends StatefulWidget {
  const VerificationProgress({super.key});

  @override
  _VerificationProgressState createState() => _VerificationProgressState();
}

class _VerificationProgressState extends State<VerificationProgress> 
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  final List<String> _verificationSteps = [
    "Processing fingerprints...",
    "Extracting unique features...",
    "Comparing with database...",
    "Analyzing match quality...",
    "Almost done...",
  ];
  int _currentStep = 0;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
    
    // Cycle through verification steps
    _startStepCycle();
  }
  
  void _startStepCycle() {
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _currentStep = (_currentStep + 1) % _verificationSteps.length;
        });
        _startStepCycle();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black.withOpacity(0.85),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Animated fingerprint scanner graphic
            Stack(
              alignment: Alignment.center,
              children: [
                // Outer scanning circle
                AnimatedBuilder(
                  animation: _controller,
                  builder: (_, child) {
                    return Transform.rotate(
                      angle: _controller.value * 2 * math.pi,
                      child: Container(
                        width: 200,
                        height: 200,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: Colors.blue.withOpacity(0.5),
                            width: 4,
                            strokeAlign: BorderSide.strokeAlignOutside,
                          ),
                          gradient: SweepGradient(
                            colors: [
                              Colors.blue.withOpacity(0),
                              Colors.blue,
                              Colors.blue.withOpacity(0),
                            ],
                            stops: const [0.0, 0.5, 1.0],
                          ),
                        ),
                      ),
                    );
                  },
                ),
                
                // Middle pulsing circle
                TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 0.8, end: 1.2),
                  duration: const Duration(seconds: 1),
                  builder: (_, value, __) {
                    return Container(
                      width: 150 * value,
                      height: 150 * value,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.blue.withOpacity(0.2),
                      ),
                    );
                  },
                  onEnd: () {
                    setState(() {});  // Trigger rebuild to restart animation
                  },
                ),
                
                // Fingerprint icon
                const Icon(
                  Icons.fingerprint,
                  size: 120,
                  color: Colors.white,
                ),
              ],
            ),
            
            const SizedBox(height: 40),
            
            // Status text
            Text(
              _verificationSteps[_currentStep],
              style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            
            const SizedBox(height: 30),
            
            // Progress indicator
            const SizedBox(
              width: 250,
              child: LinearProgressIndicator(
                minHeight: 8,
                backgroundColor: Colors.grey,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
              ),
            ),
            
            const SizedBox(height: 40),
            
            // Please wait text
            const Text(
              "Please wait while we verify your identity",
              style: TextStyle(
                color: Colors.white70,
                fontSize: 16,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
} 