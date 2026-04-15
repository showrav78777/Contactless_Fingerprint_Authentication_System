import 'package:flutter/material.dart';
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
          ListTile(
            leading: const Icon(Icons.handshake, color: Color(0xFF3B82F6)),
            title: const Text(
              'Hand Tracking',
              style: TextStyle(color: Colors.white),
            ),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/hand_tracking');
            },
          ),
          const Divider(color: Color(0xFF334155)),
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