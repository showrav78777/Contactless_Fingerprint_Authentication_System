import 'package:flutter/material.dart';
import 'login.dart'; // Import the Login screen

class IdEntryScreen extends StatefulWidget {
  const IdEntryScreen({super.key});

  @override
  _IdEntryScreenState createState() => _IdEntryScreenState();
}

class _IdEntryScreenState extends State<IdEntryScreen> {
  final TextEditingController _idController = TextEditingController();

  void _onContinuePressed() {
    String personId = _idController.text.trim();
    if (personId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter your ID'), backgroundColor: Colors.red),
      );
    } else {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => Login(personId: personId),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Enter Your ID')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Please enter your Person ID to proceed with login',
              style: TextStyle(fontSize: 18),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _idController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Person ID',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _onContinuePressed,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 15),
              ),
              child: const Text('Continue', style: TextStyle(fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _idController.dispose();
    super.dispose();
  }
}