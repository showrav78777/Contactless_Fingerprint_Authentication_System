//import 'package:finger/viewimages.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:finger/config.dart';
import 'package:finger/settings.dart';

import 'camera.dart';
import 'id_entry_screen.dart';
import 'info_screen.dart';
import 'login.dart';
import 'splash_screen.dart';
import 'viewimages.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Load saved IP configuration
  await AppConfig.loadSavedIp();
  
  // Set system UI overlay style for a more immersive dark theme
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: Color(0xFF0F172A),
    systemNavigationBarIconBrightness: Brightness.light,
  ));
  
  runApp(const FingerprintApp());
}

class FingerprintApp extends StatefulWidget {
  const FingerprintApp({super.key});

  @override
  State<FingerprintApp> createState() => _FingerprintAppState();
}

class _FingerprintAppState extends State<FingerprintApp> {
  // Listen for IP changes
  @override
  void initState() {
    super.initState();
    AppConfig.onIpChanged.listen((_) {
      // Force a rebuild when the IP changes
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    AppConfig.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fingerprint Authentication',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        primaryColor: const Color(0xFF3B82F6),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3B82F6),
          secondary: Color(0xFF10B981),
          surface: Color(0xFF1E293B),
        ),
      ),
     initialRoute: '/',
  routes: {
    '/': (context) => const SplashScreen(),
    '/welcome': (context) => const WelcomePage(),
    '/id_entry': (context) => const IdEntryScreen(),
    '/login': (context) {
      final String personId = ModalRoute.of(context)?.settings.arguments as String? ?? '1'; // Default to '1' if null
      return Login(personId: personId);
    },
    
    '/logininfo': (context) => const InfoScreen(title: '', message: '', personId: ''),
    '/main': (context) => const WelcomePage(),
    '/camera': (context) => const CameraScreen(),
    '/info': (context) {
          final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
          return InfoScreen(
            title: args?['title'] ?? 'Registration Complete',
            message: args?['message'] ?? 'Your fingerprints have been successfully registered.',
            personId: args?['personId'],
          );},
    '/view_images': (context) => const ViewImages(),
    '/settings': (context) => const SettingsScreen(),
  },
    );
  }
}

class WelcomePage extends StatefulWidget {
  const WelcomePage({super.key});

  @override
  State<WelcomePage> createState() => _WelcomePageState();
}

class _WelcomePageState extends State<WelcomePage> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  void _navigateToRegister() {
    Navigator.pushNamed(context, '/camera');
  }

  void _navigateToLogin() {
    Navigator.pushNamed(context, '/id_entry');
  }
  
  void _openDrawer() {
    _scaffoldKey.currentState?.openDrawer();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      drawer: const AppDrawer(),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [
              Color(0xFF0F172A), // Very dark blue
              Color(0xFF1E293B), // Dark slate blue
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // App bar with hamburger menu
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                child: Row(
                  children: [
                    // Hamburger menu
                    IconButton(
                      icon: const Icon(
                        Icons.menu,
                        color: Colors.white,
                        size: 28,
                      ),
                      onPressed: _openDrawer,
                    ),
                    const Spacer(),
                    // App title
                    const Text(
                      'Contactless Fingerprint',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Spacer(),
                    // Settings icon
                    IconButton(
                      icon: const Icon(
                        Icons.settings,
                        color: Colors.white,
                        size: 24,
                      ),
                      onPressed: () {
                        Navigator.pushNamed(context, '/settings');
                      },
                    ),
                  ],
                ),
              ),
              
              // Main content
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(height: 40),
                        
                        // App Logo
                        Container(
                          width: 140,
                          height: 140,
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E293B),
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF3B82F6).withOpacity(0.3),
                                blurRadius: 20,
                                spreadRadius: 2,
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
                          ),
                        ),
                        
                        const SizedBox(height: 40),
                        
                        // Welcome Text
                        const Text(
                          'Welcome to Contactless Fingerprint',
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            letterSpacing: 0.5,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        
                        const SizedBox(height: 16),
                        
                        Container(
                          width: 50,
                          height: 3,
                          decoration: BoxDecoration(
                            color: const Color(0xFF3B82F6),
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                        
                        const SizedBox(height: 16),
                        
                        const Text(
                          'Capture and authenticate fingerprints contactlessly with AI-powered technology',
                          style: TextStyle(
                            fontSize: 16,
                            color: Color(0xFF94A3B8),
                            height: 1.5,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        
                        const SizedBox(height: 60),
                        
                        // Register Button
                        HDButton(
                          text: 'Register',
                          color: const Color(0xFF3B82F6), // Bright blue
                          icon: Icons.fingerprint,
                          onPressed: _navigateToRegister,
                        ),
                        
                        const SizedBox(height: 20),
                        
                        // Login Button
                        HDButton(
                          text: 'Login',
                          color: const Color(0xFF10B981), // Green
                          icon: Icons.login,
                          onPressed: _navigateToLogin,
                        ),
                        
                        const SizedBox(height: 60),
                        
                        // Footer
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              width: 30,
                              height: 1,
                              color: const Color(0xFF64748B),
                            ),
                            const SizedBox(width: 10),
                            const Text(
                              'Powered by Flutter & Django',
                              style: TextStyle(
                                fontSize: 14,
                                color: Color(0xFF64748B),
                                letterSpacing: 0.5,
                              ),
                            ),
                            const SizedBox(width: 10),
                            Container(
                              width: 30,
                              height: 1,
                              color: const Color(0xFF64748B),
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      backgroundColor: const Color(0xFF1E293B),
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(
              color: Color(0xFF0F172A),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 70,
                  height: 70,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF3B82F6).withOpacity(0.3),
                        blurRadius: 10,
                        spreadRadius: 1,
                      ),
                    ],
                  ),
                  child: Image.asset(
                    'assets/2313181.png',
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 15),
                const Text(
                  'Fingerprint System',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Text(
                  'Contactless Authentication',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
          // Dashboard
          ListTile(
            leading: const Icon(Icons.dashboard, color: Color(0xFF3B82F6)),
            title: const Text(
              'Dashboard',
              style: TextStyle(color: Colors.white),
            ),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushReplacementNamed(context, '/welcome');
            },
          ),
          // View Database Images
          ListTile(
            leading: const Icon(Icons.fingerprint, color: Color(0xFF3B82F6)),
            title: const Text(
              'Database Images',
              style: TextStyle(color: Colors.white),
            ),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/view_images');
            },
          ),
          // Register
          ListTile(
            leading: const Icon(Icons.app_registration, color: Color(0xFF3B82F6)),
            title: const Text(
              'Register New User',
              style: TextStyle(color: Colors.white),
            ),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/camera');
            },
          ),
          // Login
          ListTile(
            leading: const Icon(Icons.login, color: Color(0xFF3B82F6)),
            title: const Text(
              'Login',
              style: TextStyle(color: Colors.white),
            ),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/login');
            },
          ),
          const Divider(color: Color(0xFF334155)),
          // Settings
          ListTile(
            leading: const Icon(Icons.settings, color: Color(0xFF3B82F6)),
            title: const Text(
              'Settings',
              style: TextStyle(color: Colors.white),
            ),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/settings');
            },
          ),
          // About
          ListTile(
            leading: const Icon(Icons.info_outline, color: Color(0xFF3B82F6)),
            title: const Text(
              'About',
              style: TextStyle(color: Colors.white),
            ),
            onTap: () {
              Navigator.pop(context);
              showAboutDialog(
                context: context,
                applicationName: 'Contactless Fingerprint',
                applicationVersion: '1.0.0',
                applicationIcon: Image.asset(
                  'assets/2313181.png',
                  width: 50,
                  height: 50,
                ),
                children: [
                  const Text(
                    'A contactless fingerprint authentication system using AI-powered technology.',
                    style: TextStyle(color: Color.fromARGB(221, 255, 255, 255)),
                  ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

class HDButton extends StatelessWidget {
  final String text;
  final Color color;
  final IconData icon;
  final VoidCallback onPressed;

  const HDButton({
    super.key,
    required this.text,
    required this.color,
    required this.icon,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 270,
      height: 60,
      decoration: BoxDecoration(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(30),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.3),
            blurRadius: 15,
            spreadRadius: -5,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Material(
        color: color,
        borderRadius: BorderRadius.circular(30),
        child: InkWell(
          borderRadius: BorderRadius.circular(30),
          onTap: onPressed,
          splashColor: Colors.white.withOpacity(0.1),
          highlightColor: Colors.white.withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 15),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  icon,
                  color: Colors.white,
                  size: 24,
                ),
                const SizedBox(width: 12),
                Text(
                  text,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
