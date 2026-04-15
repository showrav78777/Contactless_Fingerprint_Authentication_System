import 'package:shared_preferences/shared_preferences.dart';
import 'dart:async';

class AppConfig {
  static const String defaultServerIp = '0af13edb8cf6.ngrok-free.ap';
  static String serverIp = defaultServerIp;
  static String get serverUrl => serverIp;
  static String get baseApiUrl => 'https://$serverUrl/api';
  
  // Stream controller for IP changes
  static final _ipChangeController = StreamController<String>.broadcast();
  static Stream<String> get onIpChanged => _ipChangeController.stream;

  // Load saved IP from SharedPreferences
  static Future<void> loadSavedIp() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedIp = prefs.getString('server_ip');
      if (savedIp != null && savedIp.isNotEmpty) {
        serverIp = savedIp;
      } else {
        // If no saved IP, use the default
        serverIp = defaultServerIp;
      }
    } catch (e) {
      print('Error loading saved IP: $e');
      // If there's an error, fall back to default
      serverIp = defaultServerIp;
    }
  }

  // Save IP to SharedPreferences
  static Future<void> saveServerIp(String ip) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final oldIp = serverIp;
      
      serverIp = ip;
      await prefs.setString('server_ip', serverIp);
      
      // Notify listeners if the IP changed
      if (oldIp != ip) {
        _ipChangeController.add(serverIp);
      }
    } catch (e) {
      print('Error saving server IP: $e');
    }
  }
  
  // Dispose resources
  static void dispose() {
    _ipChangeController.close();
  }
} 