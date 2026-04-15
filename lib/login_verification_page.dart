import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:finger/config.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LoginVerificationPage extends StatefulWidget {
  final String personId;

  const LoginVerificationPage({super.key, required this.personId});

  @override
  _LoginVerificationPageState createState() => _LoginVerificationPageState();
}

class _LoginVerificationPageState extends State<LoginVerificationPage> {
  bool _isVerifying = true;
  Map<String, dynamic>? _verificationResult;

  @override
  void initState() {
    super.initState();
    print('LoginVerificationPage initState: Starting verification for personId: ${widget.personId}');
    _verifyLogin();
  }

  Future<String?> _fetchCsrfToken() async {
    try {
      print('Fetching CSRF token in LoginVerificationPage...');
      final response = await http.get(
        Uri.parse('${AppConfig.baseApiUrl}/get-csrf-token/'),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        String csrfToken = data['csrfToken'];
        SharedPreferences prefs = await SharedPreferences.getInstance();
        await prefs.setString('csrf_token', csrfToken);
        print('CSRF token fetched: $csrfToken');
        return csrfToken;
      }
      print('Failed to fetch CSRF token: ${response.statusCode} - ${response.body}');
      return null;
    } catch (e) {
      print('Error fetching CSRF token: $e');
      SharedPreferences prefs = await SharedPreferences.getInstance();
      return prefs.getString('csrf_token')?.isNotEmpty == true ? prefs.getString('csrf_token') : null;
    }
  }

  Future<void> _verifyLogin() async {
    String? csrfToken = await _fetchCsrfToken();
    if (csrfToken == null) {
      if (mounted) {
        setState(() {
          _isVerifying = false;
          _verificationResult = {'status': 'error', 'message': 'Server connection issue'};
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Server connection issue - please try again'), backgroundColor: Colors.orange),
        );
      }
      return;
    }

    try {
      final uri = Uri.parse('${AppConfig.baseApiUrl}/verify-login/');
      print('Sending POST to $uri with body: {"person_id": "${widget.personId}"}');
      final response = await http.post(
        uri,
        headers: {
          'X-CSRFToken': csrfToken,
          'Cookie': 'csrftoken=$csrfToken',
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: json.encode({'person_id': widget.personId}),
      ).timeout(const Duration(seconds: 300));

      if (!mounted) return;

      print('Verify login response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        print('Verification result: $result');
        setState(() {
          _isVerifying = false;
          _verificationResult = result;
        });
      } else {
        print('Verification failed: ${response.statusCode} - ${response.reasonPhrase}');
        setState(() {
          _isVerifying = false;
          _verificationResult = {'status': 'error', 'message': 'Verification failed: ${response.reasonPhrase}'};
        });
      }
    } catch (e) {
      print('Error verifying login: $e');
      if (mounted) {
        setState(() {
          _isVerifying = false;
          _verificationResult = {'status': 'error', 'message': 'Error: $e'};
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: _isVerifying
            ? const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Colors.white),
                  SizedBox(height: 20),
                  Text(
                    'Verifying your fingerprints...',
                    style: TextStyle(color: Colors.white, fontSize: 20),
                  ),
                ],
              )
            : _verificationResult != null
                ? _buildResultWidget()
                : const Text('Something went wrong', style: TextStyle(color: Colors.white)),
      ),
    );
  }

  Widget _buildResultWidget() {
    String personId = _verificationResult!['status'] == 'success' ? _verificationResult!['person_id'].toString() : 'Unknown';
    String statusMessage = _verificationResult!['status'] == 'success' ? 'Login Successful!' : 'Verification Failed';
    String message = _verificationResult!['status'] == 'success'
        ? 'You have been successfully logged in.'
        : _verificationResult!['message'] ?? 'Login attempt failed. Please try again.';

    return Column(
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
                color: _verificationResult!['status'] == 'success' ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _verificationResult!['status'] == 'success' ? Icons.check_circle_outline : Icons.error_outline,
                color: _verificationResult!['status'] == 'success' ? Colors.green : Colors.red,
                size: 100,
              ),
            ),
          ),
        ),
        const SizedBox(height: 40),
        Text(
          statusMessage,
          style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),
        Text(
          'Person ID: $personId',
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
                      gradient: LinearGradient(
                        colors: _verificationResult!['status'] == 'success'
                            ? [Colors.green.shade300, Colors.green]
                            : [Colors.red.shade300, Colors.red],
                      ),
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
          message,
          style: const TextStyle(color: Colors.white70, fontSize: 16),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 20),
        ElevatedButton(
          onPressed: () {
            if (_verificationResult!['status'] == 'success') {
              print('Continue button pressed, navigating to /welcome with personId: $personId');
              Navigator.pushReplacementNamed(context, '/welcome', arguments: personId); // Pass only personId as String
            } else {
              print('Retry button pressed, popping back');
              Navigator.pop(context);
            }
          },
          child: Text(_verificationResult!['status'] == 'success' ? 'Continue' : 'Retry'),
        ),
      ],
    );
  }
}