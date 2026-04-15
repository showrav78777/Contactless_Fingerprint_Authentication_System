import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:finger/config.dart';
import 'package:http/http.dart' as http;

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _ipController = TextEditingController();
  bool _isTesting = false;
  String _connectionStatus = '';
  bool _isConnectionOk = false;
  String _deviceIpAddress = 'Loading...';
  bool _isLoadingDeviceIp = true;

  @override
  void initState() {
    super.initState();
    // Set the default ngrok URL from AppConfig
    _ipController.text = AppConfig.defaultServerIp;
    _getDeviceIpAddress();
    // Test connection automatically when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _testConnection();
    });
  }

  Future<void> _getDeviceIpAddress() async {
    if (!mounted) return;
    
    setState(() {
      _isLoadingDeviceIp = true;
    });
    
    try {
      // Use only NetworkInterface which is more reliable
      List<String> addresses = [];
      
      for (var interface in await NetworkInterface.list()) {
        // Skip loopback interfaces
        if (interface.name.contains('lo')) {
          continue;
        }
        
        for (var addr in interface.addresses) {
          if (addr.type == InternetAddressType.IPv4) {
            // Skip localhost addresses
            if (!addr.address.startsWith('127.')) {
              addresses.add('${addr.address} (${interface.name})');
            }
          }
        }
      }
      
      if (!mounted) return;
      
      if (addresses.isNotEmpty) {
        setState(() {
          _deviceIpAddress = addresses.join('\n');
          _isLoadingDeviceIp = false;
        });
      } else {
        setState(() {
          _deviceIpAddress = 'No IP address found';
          _isLoadingDeviceIp = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      
      setState(() {
        _deviceIpAddress = 'Error getting IP: ${e.toString().split('\n').first}';
        _isLoadingDeviceIp = false;
      });
      print('Error getting device IP: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() {
                _ipController.text = AppConfig.defaultServerIp;
              });
              _testConnection();
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Device IP Address Section
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: Colors.blue.withOpacity(0.5),
                    width: 1,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.phone_android, color: Colors.blue),
                        const SizedBox(width: 8),
                        const Text(
                          'Device IP Address',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Spacer(),
                        if (_isLoadingDeviceIp)
                          const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    _buildIpAddressList(),
                    const SizedBox(height: 4),
                    const Text(
                      'Use this IP in your server configuration to connect to this device',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Server Configuration Section
              const Text(
                'Server Configuration',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _ipController,
                decoration: const InputDecoration(
                  labelText: 'Server URL',
                  border: OutlineInputBorder(),
                  hintText: AppConfig.defaultServerIp,
                  helperText: 'Default server URL will be used automatically',
                ),
                keyboardType: TextInputType.text,
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  ElevatedButton(
                    onPressed: _testConnection,
                    child: _isTesting 
                      ? const SizedBox(
                          width: 20, 
                          height: 20, 
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : const Text('Test Connection'),
                  ),
                  const SizedBox(width: 16),
                  ElevatedButton(
                    onPressed: _saveSettings,
                    child: const Text('Save Settings'),
                  ),
                ],
              ),
              if (_connectionStatus.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 16.0),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: _isConnectionOk ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: _isConnectionOk ? Colors.green : Colors.red,
                        width: 1,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _isConnectionOk ? Icons.check_circle : Icons.error,
                          color: _isConnectionOk ? Colors.green : Colors.red,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _connectionStatus,
                            style: TextStyle(
                              color: _isConnectionOk ? Colors.green : Colors.red,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 24),
              const Text(
                'Current Configuration:',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text('Server URL: https://${AppConfig.serverUrl}'),
              Text('API Base URL: ${AppConfig.baseApiUrl}'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIpAddressList() {
    if (_isLoadingDeviceIp) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 8.0),
        child: Text('Detecting IP addresses...'),
      );
    }
    
    if (_deviceIpAddress.startsWith('Error') || 
        _deviceIpAddress.startsWith('No IP')) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 8.0),
        child: Text(
          _deviceIpAddress,
          style: const TextStyle(color: Colors.red),
        ),
      );
    }
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: _deviceIpAddress.split('\n').map((ip) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 4.0),
            child: Row(
              children: [
                const Icon(Icons.circle, size: 8, color: Colors.blue),
                const SizedBox(width: 8),
                Expanded(child: Text(ip, style: const TextStyle(fontSize: 14))),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Future<void> _testConnection() async {
    setState(() {
      _isTesting = true;
      _connectionStatus = 'Testing connection...';
      _isConnectionOk = false;
    });

    String ip = _ipController.text.trim();
    
    // If empty, use default server IP
    if (ip.isEmpty) {
      ip = AppConfig.defaultServerIp;
      _ipController.text = ip;
    }
    
    try {
      final response = await http.get(
        Uri.parse('https://$ip/api/check-server/'),
      ).timeout(const Duration(seconds: 5));
      
      if (!mounted) return;
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _connectionStatus = 'Connection successful! Server: ${data['server_ip']}';
          _isConnectionOk = true;
        });

        // If connection is successful, save the IP
        await AppConfig.saveServerIp(ip);
      } else {
        setState(() {
          _connectionStatus = 'Connection failed: HTTP ${response.statusCode}';
          _isConnectionOk = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _connectionStatus = 'Connection error: ${e.toString().split(':').first}';
        _isConnectionOk = false;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isTesting = false;
        });
      }
    }
  }

  Future<void> _saveSettings() async {
    final ip = _ipController.text.trim();
    
    if (ip.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Server URL cannot be empty')),
      );
      return;
    }
    
    // Save the settings
    await AppConfig.saveServerIp(ip);
    
    // Update the UI to show the new values
    if (!mounted) return;
    setState(() {});
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Settings saved successfully'),
        backgroundColor: Colors.green,
      ),
    );
    
    // Show a dialog asking if the user wants to restart the app
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Settings Updated'),
        content: const Text(
          'The server settings have been updated. It\'s recommended to restart the app for the changes to take full effect. Would you like to return to the home screen?'
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
            },
            child: const Text('STAY HERE'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.popUntil(context, ModalRoute.withName('/welcome')); // Go to home
            },
            child: const Text('GO TO HOME'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _ipController.dispose();
    super.dispose();
  }
} 