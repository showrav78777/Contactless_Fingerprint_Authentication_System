import 'dart:convert';
import 'dart:async';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:finger/config.dart';
import 'package:finger/login_verification_page.dart';
import 'FingerOutlinePainter.dart';

class Login extends StatefulWidget {
  final String personId;

  const Login({super.key, required this.personId});

  @override
  _LoginState createState() => _LoginState();
}

class _LoginState extends State<Login> {
  late CameraController _cameraController;
  bool _isCameraInitialized = false;
  bool _isProcessing = false;
  bool _isFlashOn = true;
  final List<String> _fingerNames = ['left thumb', '4 left fingers', 'right thumb', '4 right fingers'];
  int _currentIndex = 0;
  double _minAvailableZoom = 1.0;
  double _maxAvailableZoom = 1.0;
  double _currentZoomLevel = 1.0;
  bool _isFocusing = false;

  @override
  void initState() {
    super.initState();
    print('Login initState: Starting camera initialization for personId: ${widget.personId}');
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        print('No cameras available');
        return;
      }
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

      print('Initializing camera...');
      await _cameraController.initialize();
      await _cameraController.setFlashMode(FlashMode.torch);
      await _cameraController.setFocusMode(FocusMode.auto);
      await _cameraController.setExposureMode(ExposureMode.auto);

      _minAvailableZoom = await _cameraController.getMinZoomLevel();
      _maxAvailableZoom = await _cameraController.getMaxZoomLevel();
      _currentZoomLevel = 1.0;
      await _cameraController.setZoomLevel(_currentZoomLevel);

      if (mounted) {
        setState(() => _isCameraInitialized = true);
        print('Camera initialized successfully');
      }
    } catch (e) {
      print('Error initializing camera: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Camera error: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<String?> _fetchCsrfToken() async {
    try {
      print('Fetching CSRF token...');
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
      final cachedToken = prefs.getString('csrf_token');
      if (cachedToken != null && cachedToken.isNotEmpty) {
        print('Using cached token: $cachedToken');
        return cachedToken;
      }
      return null;
    }
  }

  Future<void> _captureAndUploadImage() async {
    if (!_cameraController.value.isInitialized || _isProcessing) {
      print('Camera not initialized or processing, skipping capture');
      return;
    }

    setState(() => _isProcessing = true);
    print('Capturing image for ${_fingerNames[_currentIndex]} (Index: $_currentIndex)...');

    bool wasFlashOn = _isFlashOn;

    try {
      if (_isFlashOn) {
        print('Turning off flash for capture...');
        await _cameraController.setFlashMode(FlashMode.off);
        setState(() => _isFlashOn = false);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Processing...'), duration: Duration(seconds: 1)),
        );
      }

      final XFile imageFile = await _cameraController.takePicture();
      print('Image captured: ${imageFile.path}');

      if (!mounted) {
        print('Widget not mounted after capture, aborting');
        return;
      }

      String? csrfToken = await _fetchCsrfToken();
      if (csrfToken == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Server connection issue - please try again'), backgroundColor: Colors.orange),
          );
          setState(() => _isProcessing = false);
        }
        return;
      }

      final uri = Uri.parse('${AppConfig.baseApiUrl}/upload/');
      final request = http.MultipartRequest('POST', uri);
      request.files.add(await http.MultipartFile.fromPath('images', imageFile.path));
      request.fields.addAll({
        'finger_name': _fingerNames[_currentIndex],
        'is_login': 'true',
      });
      request.headers.addAll({
        'X-CSRFToken': csrfToken,
        'Cookie': 'csrftoken=$csrfToken',
        'Accept': 'application/json',
      });

      print('Uploading image to $uri...');
      final response = await request.send().timeout(
        const Duration(seconds: 30),
        onTimeout: () => http.StreamedResponse(Stream.fromIterable([]), 408, reasonPhrase: 'Request Timeout'),
      );

      String responseBody = await response.stream.bytesToString();
      print('Upload response: ${response.statusCode} - $responseBody');

      if (!mounted) {
        print('Widget not mounted after upload, aborting');
        return;
      }

      if (response.statusCode == 200) {
        print('Image uploaded successfully');
        setState(() {
          if (_currentIndex < _fingerNames.length - 1) {
            _currentIndex++;
            print('Moving to next finger: ${_fingerNames[_currentIndex]}');
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Next: ${_fingerNames[_currentIndex]}'), backgroundColor: Colors.green),
            );
            if (wasFlashOn && !_isFlashOn) {
              _cameraController.setFlashMode(FlashMode.torch).then((_) {
                if (mounted) setState(() => _isFlashOn = true);
                print('Flash restored');
              }).catchError((e) => print('Error restoring flash: $e'));
            }
          } else {
            print('All images uploaded (Index: $_currentIndex), shutting down camera...');
            _shutdownCameraAndNavigate();
          }
        });
      } else if (response.statusCode == 408) {
        print('Upload timed out');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Upload timed out - please try again'), backgroundColor: Colors.orange),
          );
        }
      } else {
        print('Failed to upload image: ${response.reasonPhrase}');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to upload: ${response.reasonPhrase}'), backgroundColor: Colors.red),
          );
        }
      }
    } catch (e) {
      print('Error capturing/uploading image: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted && wasFlashOn && !_isFlashOn && _currentIndex < _fingerNames.length - 1) {
        await _cameraController.setFlashMode(FlashMode.torch);
        setState(() => _isFlashOn = true);
        print('Flash restored in finally');
      }
      if (mounted) {
        setState(() => _isProcessing = false);
        print('Processing state reset');
      }
    }
  }

  Future<void> _shutdownCameraAndNavigate() async {
  try {
    print('Turning off flash...');
    await _cameraController.setFlashMode(FlashMode.off).timeout(const Duration(seconds: 2));
    // await _cameraController.dispose().timeout(const Duration(seconds: 5));
    print('Skipping disposal for testing');
  } catch (e) {
    print('Error during camera shutdown: $e');
  } finally {
    if (mounted) {
      setState(() => _isCameraInitialized = false);
      print('Navigating to LoginVerificationPage with personId: ${widget.personId}');
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (context) => LoginVerificationPage(personId: widget.personId)));
    }
  }
}

  Future<void> _onTapToFocus(TapDownDetails details, BoxConstraints constraints) async {
    if (_cameraController.value.isInitialized && !_isFocusing) {
      setState(() => _isFocusing = true);
      final double x = details.localPosition.dx / constraints.maxWidth;
      final double y = details.localPosition.dy / constraints.maxHeight;
      try {
        await _cameraController.setFocusPoint(Offset(x, y));
        await _cameraController.setExposurePoint(Offset(x, y));
        await Future.delayed(const Duration(seconds: 2));
        if (mounted) {
          await _cameraController.setFocusMode(FocusMode.auto);
          await _cameraController.setExposureMode(ExposureMode.auto);
          setState(() => _isFocusing = false);
        }
      } catch (e) {
        print('Error setting focus: $e');
        if (mounted) setState(() => _isFocusing = false);
      }
    }
  }

  Future<void> _toggleFlash() async {
    if (!_cameraController.value.isInitialized) return;
    try {
      _isFlashOn = !_isFlashOn;
      await _cameraController.setFlashMode(_isFlashOn ? FlashMode.torch : FlashMode.off);
      if (mounted) {
        setState(() {});
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Flash ${_isFlashOn ? 'On' : 'Off'}'), duration: const Duration(seconds: 1)),
        );
      }
    } catch (e) {
      print('Error toggling flash: $e');
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
                  padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top + 16, bottom: 16),
                  child: Text(
                    'Capturing: ${_fingerNames[_currentIndex]} (ID: ${widget.personId})',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
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
                        child: ClipRRect(borderRadius: BorderRadius.circular(12), child: CameraPreview(_cameraController)),
                      ),
                      if (_isFocusing)
                        Center(
                          child: Container(
                            width: 80,
                            height: 80,
                            decoration: BoxDecoration(border: Border.all(color: Colors.yellow, width: 2), borderRadius: BorderRadius.circular(40)),
                          ),
                        ),
                      CustomPaint(painter: FingerOutlinePainter(_fingerNames[_currentIndex]), size: Size.infinite),
                      Positioned(
                        right: 16.0,
                        top: 16.0,
                        child: Column(
                          children: [
                            Container(
                              decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(20)),
                              padding: const EdgeInsets.all(4),
                              child: Column(
                                children: [
                                  IconButton(
                                    icon: const Icon(Icons.zoom_in, color: Colors.white),
                                    onPressed: () async {
                                      if (_currentZoomLevel < _maxAvailableZoom) {
                                        _currentZoomLevel = (_currentZoomLevel + 0.1).clamp(_minAvailableZoom, _maxAvailableZoom);
                                        await _cameraController.setZoomLevel(_currentZoomLevel);
                                        if (mounted) setState(() {});
                                      }
                                    },
                                  ),
                                  Text('${_currentZoomLevel.toStringAsFixed(1)}x', style: const TextStyle(color: Colors.white)),
                                  IconButton(
                                    icon: const Icon(Icons.zoom_out, color: Colors.white),
                                    onPressed: () async {
                                      if (_currentZoomLevel > _minAvailableZoom) {
                                        _currentZoomLevel = (_currentZoomLevel - 0.1).clamp(_minAvailableZoom, _maxAvailableZoom);
                                        await _cameraController.setZoomLevel(_currentZoomLevel);
                                        if (mounted) setState(() {});
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
                          decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(20)),
                          child: IconButton(
                            icon: const Icon(Icons.center_focus_strong, color: Colors.white),
                            onPressed: () async {
                              try {
                                final focusMode = _cameraController.value.focusMode;
                                await _cameraController.setFocusMode(focusMode == FocusMode.auto ? FocusMode.locked : FocusMode.auto);
                                if (mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text(focusMode == FocusMode.auto ? 'Focus locked' : 'Auto focus enabled'), duration: const Duration(seconds: 1)),
                                  );
                                }
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
                          decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(20)),
                          child: IconButton(
                            icon: Icon(_isFlashOn ? Icons.flash_on : Icons.flash_off, color: Colors.white),
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
                  padding: EdgeInsets.only(top: 20, bottom: MediaQuery.of(context).padding.bottom + 20),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      FloatingActionButton(
                        onPressed: _isProcessing ? null : _captureAndUploadImage,
                        backgroundColor: _isProcessing ? Colors.grey : Colors.white,
                        child: _isProcessing
                            ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
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
    print('Disposing Login widget...');
    _cameraController.dispose();
    super.dispose();
    print('Login widget disposed');
  }
}