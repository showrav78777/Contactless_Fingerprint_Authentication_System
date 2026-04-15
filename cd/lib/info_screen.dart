import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:finger/config.dart';
import 'package:shared_preferences/shared_preferences.dart';

class InfoScreen extends StatefulWidget {
  final String title;
  final String message;
  final String? personId;

  const InfoScreen({
    super.key,
    required this.title,
    required this.message,
    this.personId,
  });

  @override
  _InfoScreenState createState() => _InfoScreenState();
}

class _InfoScreenState extends State<InfoScreen> {
  String? _personId;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    print('InfoScreen initState: Starting person ID fetch');
    _fetchPersonId();
  }

  Future<String?> _fetchCsrfToken() async {
    try {
      print('Fetching CSRF token in InfoScreen...');
      final response = await http.get(
        Uri.parse('${AppConfig.baseApiUrl}/get-csrf-token/'),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        String csrfToken = data['csrfToken'];
        SharedPreferences prefs = await SharedPreferences.getInstance();
        await prefs.setString('csrf_token', csrfToken);
        print('CSRF Token fetched: $csrfToken');
        return csrfToken;
      }
      print('Failed to fetch CSRF token: ${response.statusCode}');
      return null;
    } catch (e) {
      print('Error fetching CSRF token: $e');
      SharedPreferences prefs = await SharedPreferences.getInstance();
      return prefs.getString('csrf_token')?.isNotEmpty == true ? prefs.getString('csrf_token') : null;
    }
  }

  Future<void> _fetchPersonId() async {
    try {
      final csrfToken = await _fetchCsrfToken();
      if (csrfToken == null) {
        if (mounted) {
          setState(() {
            _isLoading = false;
            _personId = 'Unknown (Server Error)';
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Server connection issue'), backgroundColor: Colors.orange),
          );
        }
        return;
      }

      final url = Uri.parse('${AppConfig.baseApiUrl}/get-person-id/');
      print('Fetching person ID from $url...');
      final response = await http.get(
        url,
        headers: {'X-CSRFToken': csrfToken, 'Cookie': 'csrftoken=$csrfToken'},
      ).timeout(const Duration(seconds: 15));

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('Person ID response: $data');
        setState(() {
          _isLoading = false;
          _personId = data['person_id'].toString();
        });
      } else {
        print('Failed to fetch person ID: ${response.statusCode} - ${response.body}');
        setState(() {
          _isLoading = false;
          _personId = 'Unknown (Server Error: ${response.reasonPhrase})';
        });
      }
    } catch (e) {
      print('Error fetching person ID: $e');
      if (mounted) {
        setState(() {
          _isLoading = false;
          _personId = 'Unknown (Error: $e)';
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error fetching person ID: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: _isLoading
            ? const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Colors.white),
                  SizedBox(height: 20),
                  Text(
                    'Processing Registration...',
                    style: TextStyle(color: Colors.white, fontSize: 20),
                  ),
                ],
              )
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  TweenAnimationBuilder<double>(
                    tween: Tween<double>(begin: 0.0, end: 1.0),
                    duration: const Duration(milliseconds: 800),
                    builder: (_, value, __) => Transform.scale(
                      scale: value,
                      child: Container(
                        width: 120,
                        height: 120,
                        decoration: BoxDecoration(
                          color: Colors.green.withOpacity(0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.check_circle_outline, color: Colors.green, size: 100),
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),
                  Text(
                    widget.title,
                    style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'Person ID: ${_personId ?? "Unknown"}',
                    style: const TextStyle(color: Colors.white, fontSize: 18),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 30),
                  SizedBox(
                    width: 250,
                    child: Stack(
                      children: [
                        Container(height: 8, decoration: BoxDecoration(color: Colors.grey[800], borderRadius: BorderRadius.circular(4))),
                        TweenAnimationBuilder<double>(
                          tween: Tween<double>(begin: 0.0, end: 1.0),
                          duration: const Duration(seconds: 3),
                          builder: (_, value, __) => FractionallySizedBox(
                            widthFactor: value,
                            child: Container(
                              height: 8,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(colors: [Colors.green.shade300, Colors.green]),
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 40),
                  Text(
                    widget.message,
                    style: const TextStyle(color: Colors.white70, fontSize: 16),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () {
                      print('Continue button pressed, navigating to /welcome');
                      Navigator.pushReplacementNamed(context, '/welcome', arguments: _personId ?? 'Unknown');
                    },
                    child: const Text('Continue'),
                  ),
                ],
              ),
      ),
    );
  }
}