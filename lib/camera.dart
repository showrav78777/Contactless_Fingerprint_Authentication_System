import 'dart:convert';
import 'dart:async';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:finger/config.dart';
import 'package:finger/info_screen.dart';

import 'FingerOutlinePainter.dart'; // Ensure InfoScreen is imported

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  _CameraScreenState createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  late CameraController _cameraController;
  bool _isCameraInitialized = false;
  bool _isProcessing = false;
  bool _isFlashOn = true;
  final List<String> _fingerNames = [
    'left thumb',
    '4 left fingers',
    'right thumb',
    '4 right fingers'
  ];
  int _currentIndex = 0;
  double _minAvailableZoom = 1.0;
  double _maxAvailableZoom = 1.0;
  double _currentZoomLevel = 1.0;
  bool _isFocusing = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      final backCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      
      _cameraController = CameraController(
        backCamera,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      try {
        await _cameraController.initialize();
        await _cameraController.setFlashMode(FlashMode.torch);
        if (_cameraController.value.isInitialized) {
          await _cameraController.setFocusMode(FocusMode.auto);
          await _cameraController.setExposureMode(ExposureMode.auto);
          await _triggerAutoFocus();
        }
        
        _minAvailableZoom = await _cameraController.getMinZoomLevel();
        _maxAvailableZoom = await _cameraController.getMaxZoomLevel();
        _currentZoomLevel = 1.0;
        await _cameraController.setZoomLevel(_currentZoomLevel);

        if (mounted) {
          setState(() => _isCameraInitialized = true);
        }
      } catch (e) {
        print('Error initializing camera: $e');
      }
    }
  }

  Future<String?> _fetchCsrfToken() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConfig.baseApiUrl}/get-csrf-token/'),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
      ).timeout(const Duration(seconds: 120));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        String csrfToken = data['csrfToken'];
        SharedPreferences prefs = await SharedPreferences.getInstance();
        await prefs.setString('csrf_token', csrfToken);
        print('CSRF Token fetched: $csrfToken');
        return csrfToken;
      }
      print('Failed to fetch CSRF token. Status: ${response.statusCode}');
      return null;
    } catch (e) {
      print('Error fetching CSRF token: $e');
      try {
        SharedPreferences prefs = await SharedPreferences.getInstance();
        final cachedToken = prefs.getString('csrf_token');
        if (cachedToken != null && cachedToken.isNotEmpty) {
          print('Using cached token: $cachedToken');
          return cachedToken;
        }
      } catch (_) {}
      return null;
    }
  }

  Future<void> _captureAndUploadImage() async {
    if (!_cameraController.value.isInitialized || _isProcessing) return;

    setState(() => _isProcessing = true);

    bool wasFlashOn = _isFlashOn;

    

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Processing...'), duration: Duration(seconds: 1)),
      );

      await _triggerAutoFocus();
      await Future.delayed(const Duration(milliseconds: 500));

      final XFile imageFile = await _cameraController.takePicture();
try {
      if (_isFlashOn) {
        await _cameraController.setFlashMode(FlashMode.off);
        setState(() => _isFlashOn = false);
      }
      OverlayEntry overlayEntry = OverlayEntry(
        builder: (context) => Container(
          color: Colors.black.withOpacity(0.85),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(color: Colors.green),
                const SizedBox(height: 20),
                Text(
                  'Registering: ${_fingerNames[_currentIndex]}',
                  style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      );
      Overlay.of(context).insert(overlayEntry);

      String? csrfToken = await _fetchCsrfToken();
      if (csrfToken == null) {
        overlayEntry.remove();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Server connection issue'), backgroundColor: Colors.orange),
        );
        setState(() {
          _currentIndex < _fingerNames.length - 1 ? _currentIndex++ : Navigator.pop(context);
          _isProcessing = false;
        });
        return;
      }

      final uri = Uri.parse('${AppConfig.baseApiUrl}/upload/');
      final request = http.MultipartRequest('POST', uri);
      request.files.add(await http.MultipartFile.fromPath('images', imageFile.path));
      request.fields['finger_name'] = _fingerNames[_currentIndex];
      request.headers.addAll({'X-CSRFToken': csrfToken, 'Cookie': 'csrftoken=$csrfToken'});

      final response = await request.send();
      String responseBody = await response.stream.bytesToString();
      overlayEntry.remove();

      if (!mounted) return;

      if (response.statusCode == 200) {
        print("Image uploaded: $responseBody");
        setState(() {
          if (_currentIndex < _fingerNames.length - 1) {
            _currentIndex++;
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Next: ${_fingerNames[_currentIndex]}'), backgroundColor: Colors.green),
            );
          } else {
            _showFinalProcessingAnimation();
          }
        });
      } else {
        print("Upload failed: ${response.reasonPhrase}");
          ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to upload: ${response.reasonPhrase}'), backgroundColor: Colors.red),
        );
      }
    } catch (e) {
      print("Error: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted && wasFlashOn && !_isFlashOn) {
        await _cameraController.setFlashMode(FlashMode.torch);
        setState(() => _isFlashOn = true);
      }
      if (mounted) setState(() => _isProcessing = false);
    }
  }

  Future<String?> _fetchPersonId() async {
    try {
      final csrfToken = await _fetchCsrfToken() ?? '';
      final url = Uri.parse('${AppConfig.baseApiUrl}/get-person-id/');
      final response = await http.get(url, headers: {'X-CSRFToken': csrfToken}).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['person_id'].toString();
      }
      print('Failed to fetch person ID: ${response.statusCode}');
      return null;
    } catch (e) {
      print('Error fetching person ID: $e');
      return null;
    }
  }

  void _showFinalProcessingAnimation() {
    if (_isFlashOn) {
      _cameraController.setFlashMode(FlashMode.off);
      setState(() => _isFlashOn = false);
    }

    String? personId;
    _fetchPersonId().then((id) {
      if (mounted) setState(() => personId = id ?? 'Unknown');
    });

    OverlayEntry finalOverlay = OverlayEntry(
      builder: (context) => Container(
        color: Colors.black.withOpacity(0.9),
        child: Center(
          child: Column(
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
                    decoration: BoxDecoration(color: Colors.green.withOpacity(0.2), shape: BoxShape.circle),
                    child: const Icon(Icons.check_circle_outline, color: Colors.green, size: 100),
                  ),
                ),
              ),
              const SizedBox(height: 40),
              const Text(
                "Registration Complete!",
                style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              Text(
                personId != null ? "Your Person ID: $personId" : "Fetching Person ID...",
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
              const Text(
                "Your fingerprints have been successfully registered.",
                style: TextStyle(color: Colors.white70, fontSize: 16),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );

    Overlay.of(context).insert(finalOverlay);

    Future.delayed(const Duration(seconds: 5), () {
      finalOverlay.remove();
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => InfoScreen(
              title: 'Registration Complete',
              message: 'Your fingerprints have been successfully registered.',
              personId: personId ?? 'Unknown',
            ),
          ),
        );
      }
    });
  }

  Future<void> _onTapToFocus(TapDownDetails details, BoxConstraints constraints) async {
    if (_cameraController.value.isInitialized && !_isFocusing) {
      setState(() => _isFocusing = true);
      
      final double x = details.localPosition.dx / constraints.maxWidth;
      final double y = details.localPosition.dy / constraints.maxHeight;
      
      try {
        await _cameraController.setFocusPoint(Offset(x, y));
        await _cameraController.setExposurePoint(Offset(x, y));
        
        Future.delayed(const Duration(seconds: 10), () {
          if (mounted) {
            _cameraController.setFocusMode(FocusMode.auto);
            _cameraController.setExposureMode(ExposureMode.auto);
            setState(() => _isFocusing = false);
          }
        });
      } catch (e) {
        print('Error setting focus: $e');
        setState(() => _isFocusing = false);
      }
    }
  }

  Future<void> _toggleFlash() async {
    if (!_cameraController.value.isInitialized) return;
    
    try {
      _isFlashOn = !_isFlashOn;
      await _cameraController.setFlashMode(_isFlashOn ? FlashMode.torch : FlashMode.off);
      setState(() {});
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Flash ${_isFlashOn ? 'On' : 'Off'}'),
            duration: const Duration(seconds: 1),
          ),
        );
      }
    } catch (e) {
      print('Error toggling flash: $e');
    }
  }

  Future<void> _triggerAutoFocus() async {
    try {
      await _cameraController.setFocusMode(FocusMode.auto);
      await _cameraController.setFocusPoint(const Offset(0.5, 0.5));
      await Future.delayed(const Duration(milliseconds: 300));
      await _cameraController.setFocusMode(FocusMode.auto);
      print('Auto focus triggered successfully');
    } catch (e) {
      print('Error triggering auto focus: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: _isCameraInitialized
          ? Column(
              children: [
                Container(
                  color: Colors.black,
                  width: double.infinity,
                  padding: EdgeInsets.only(
                    top: MediaQuery.of(context).padding.top + 16,
                    bottom: 16,
                  ),
                    child: Text(
                      'Capturing: ${_fingerNames[_currentIndex]}',
                    textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                ),
                Expanded(
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      GestureDetector(
                        onTapDown: (details) => LayoutBuilder(
                          builder: (context, constraints) {
                            _onTapToFocus(details, constraints);
                            return Container();
                          },
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: CameraPreview(_cameraController),
                        ),
                      ),
                      if (_isFocusing)
                        Center(
                          child: Container(
                            width: 80,
                            height: 80,
                            decoration: BoxDecoration(
                              border: Border.all(color: Colors.yellow, width: 2),
                              borderRadius: BorderRadius.circular(40),


                            ),
                          ),
                        ),


                        // Finger outline guide
                      CustomPaint(
                        painter: FingerOutlinePainter(_fingerNames[_currentIndex]),
                        size: Size.infinite,
                      ),
                      
                      Positioned(
                        right: 16.0,
                        top: 16.0,
                        child: Column(
                          children: [
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.black54,
                                borderRadius: BorderRadius.circular(20),
                              ),
                              padding: const EdgeInsets.all(4),
                              child: Column(
                                children: [
                                  IconButton(
                                    icon: const Icon(Icons.zoom_in, color: Colors.white),
                                    onPressed: () async {
                                      if (_currentZoomLevel < _maxAvailableZoom) {
                                        _currentZoomLevel = (_currentZoomLevel + 0.1).clamp(
                                          _minAvailableZoom,
                                          _maxAvailableZoom,
                                        );
                                        await _cameraController.setZoomLevel(_currentZoomLevel);
                                        setState(() {});
                                      }
                                    },
                                  ),
                                  Text(
                                    '${_currentZoomLevel.toStringAsFixed(1)}x',
                                    style: const TextStyle(color: Colors.white),
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.zoom_out, color: Colors.white),
                                    onPressed: () async {
                                      if (_currentZoomLevel > _minAvailableZoom) {
                                        _currentZoomLevel = (_currentZoomLevel - 0.1).clamp(
                                          _minAvailableZoom,
                                          _maxAvailableZoom,
                                        );
                                        await _cameraController.setZoomLevel(_currentZoomLevel);
                                        setState(() {});
                                      }
                                    },
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      Positioned(
                        left: 16.0,
                        top: 16.0,
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.black54,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: IconButton(
                            icon: const Icon(Icons.center_focus_strong, color: Colors.white),
                            onPressed: () async {
                              try {
                                final focusMode = _cameraController.value.focusMode;
                                await _cameraController.setFocusMode(
                                  focusMode == FocusMode.auto ? FocusMode.locked : FocusMode.auto,
                                );
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text(
                                      focusMode == FocusMode.auto ? 'Focus locked' : 'Auto focus enabled',
                                    ),
                                    duration: const Duration(seconds: 1),
                                  ),
                                );
                              } catch (e) {
                                print('Error toggling focus mode: $e');
                              }
                            },
                          ),
                        ),
                      ),
                      Positioned(
                        left: 16.0,
                        top: 80.0,
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.black54,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: IconButton(
                            icon: Icon(
                              _isFlashOn ? Icons.flash_on : Icons.flash_off,
                              color: Colors.white,
                            ),
                            onPressed: _toggleFlash,
                          ),
                        ),
                      ),
                      if (_isProcessing)
                        Container(
                          color: Colors.black54,
                          child: const Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                CircularProgressIndicator(color: Colors.white),
                                SizedBox(height: 16),
                                Text('Processing...', style: TextStyle(color: Colors.white)),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                Container(
                  color: Colors.black,
                  width: double.infinity,
                  padding: EdgeInsets.only(
                    top: 20,
                    bottom: MediaQuery.of(context).padding.bottom + 20,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      FloatingActionButton(
                        onPressed: _isProcessing ? null : _captureAndUploadImage,
                        backgroundColor: _isProcessing ? Colors.grey : Colors.white,
                        child: _isProcessing
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2),
                              )
                            : const Icon(Icons.camera_alt, color: Colors.black),
                      ),
                    ],
                  ),
                ),
              ],
            )
          : const Center(child: CircularProgressIndicator()),
    );
  }

  @override
  void dispose() {
    _cameraController.dispose();
    super.dispose();
  }
}