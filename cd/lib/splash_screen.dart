import 'package:flutter/material.dart';
import 'dart:async';


class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  _SplashScreenState createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  late AnimationController _logoController;
  late AnimationController _scanController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _opacityAnimation;
  
  @override
  void initState() {
    super.initState();
    
    // Logo animation controller
    _logoController = AnimationController(
      duration: const Duration(milliseconds: 1800),
      vsync: this,
    );
    
    // Scanning animation controller
    _scanController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);
    
    _scaleAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _logoController,
        curve: Curves.elasticOut,
      ),
    );
    
    _opacityAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _logoController,
        curve: const Interval(0.0, 0.65, curve: Curves.easeIn),
      ),
    );
    
    _logoController.forward();
    
    // Navigate to welcome screen after animation completes
    Timer(const Duration(milliseconds: 3200), () {
      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/welcome');
      }
    });
  }
  
  @override
  void dispose() {
    _logoController.dispose();
    _scanController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A), // Very dark blue
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [
              Color(0xFF0F172A), // Dark blue
              Color(0xFF1E293B), // Dark slate blue
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Animated Logo with scanning effect
              Stack(
                alignment: Alignment.center,
                children: [
                  // Scanning circle effect
                  AnimatedBuilder(
                    animation: _scanController,
                    builder: (context, child) {
                      return Container(
                        width: 230,
                        height: 230,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: RadialGradient(
                            colors: [
                              const Color(0xFF3B82F6).withOpacity(0.6 * _scanController.value),
                              Colors.transparent,
                            ],
                            stops: const [0.7, 1.0],
                          ),
                        ),
                      );
                    }
                  ),
                  
                  // Pulsing ring
                  AnimatedBuilder(
                    animation: _scanController, 
                    builder: (context, child) {
                      return Container(
                        width: 200 + (20 * _scanController.value),
                        height: 200 + (20 * _scanController.value),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: const Color(0xFF3B82F6).withOpacity(0.5 - (0.5 * _scanController.value)),
                            width: 2,
                          ),
                        ),
                      );
                    }
                  ),
                  
                  // Main logo
                  AnimatedBuilder(
                    animation: _logoController,
                    builder: (context, child) {
                      return Opacity(
                        opacity: _opacityAnimation.value,
                        child: Transform.scale(
                          scale: _scaleAnimation.value,
                          child: child,
                        ),
                      );
                    },
                    child: Container(
                      width: 180,
                      height: 180,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF3B82F6).withOpacity(0.3),
                            blurRadius: 30,
                            spreadRadius: 5,
                          ),
                        ],
                        border: Border.all(
                          color: const Color(0xFF3B82F6).withOpacity(0.3),
                          width: 2,
                        ),
                      ),
                      child: Image.asset(
                        'assets/2313181.png',
                        color: Colors.white,
                        fit: BoxFit.contain,
                      ),
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 50),
              
              // App Name with Fade-in Animation
              AnimatedBuilder(
                animation: _logoController,
                builder: (context, child) {
                  return Opacity(
                    opacity: _opacityAnimation.value,
                    child: child,
                  );
                },
                child: Column(
                  children: [
                    const Text(
                      'Fingerprint Authentication',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      width: 50,
                      height: 3,
                      decoration: BoxDecoration(
                        color: const Color(0xFF3B82F6),
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                    const SizedBox(height: 15),
                    const Text(
                      'Secure • Fast • Reliable',
                      style: TextStyle(
                        fontSize: 16,
                        color: Color(0xFF94A3B8),
                        letterSpacing: 1.0,
                      ),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 60),
              
              // Loading indicator
              AnimatedBuilder(
                animation: _logoController,
                builder: (context, child) {
                  return Opacity(
                    opacity: _opacityAnimation.value,
                    child: const SizedBox(
                      width: 40,
                      height: 40,
                      child: CircularProgressIndicator(
                        color: Color(0xFF3B82F6),
                        backgroundColor: Color(0xFF1E293B),
                        strokeWidth: 3,
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
} 