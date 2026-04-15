import 'dart:async';
import 'dart:collection';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'dart:io';
import 'dart:math';
import 'package:image/image.dart' as img;
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'config.dart';
import 'hand_landmark_painter.dart';

class HandTrackingScreen extends StatefulWidget {
  final CameraDescription camera;
  const HandTrackingScreen({super.key, required this.camera});

  @override
  _HandTrackingScreenState createState() => _HandTrackingScreenState();
}

class _HandTrackingScreenState extends State<HandTrackingScreen> {
  late CameraController _cameraController;
  bool _isCameraInitialized = false;
  bool _isControllerReinitializing = false;
  bool _isFlashOn = true; // Always start with flash on
  double _minAvailableZoom = 1.0;
  double _maxAvailableZoom = 1.0;
  double _currentZoomLevel = 1.0;
  bool _isFocusing = false;
  List<Map<String, dynamic>> _hands = [];
  static const platform = MethodChannel('com.example/mediapipe');
  bool _isStreaming = false;
  DateTime? _lastFrameProcessed;
  Duration _frameInterval = const Duration(milliseconds: 100); // Reduced from 200ms
  bool _dialogShown = false;
  DateTime? _lastCaptureTime;
  int _retryCount = 0;
  static const int _maxRetries = 3;
  double _confidenceThreshold = 0.15; // Reduced from 0.2 for better detection
  double _handZThreshold = 0.3;
  String? _errorMessage;
  String _debugInfo = '';
  bool _isProcessing = false;
  int _frameSkipCount = 0;
  static const int _frameSkipInterval = 1; // Process every 2nd frame for better detection
  Queue<CameraImage> _frameQueue = Queue<CameraImage>();
  
  // Live stream result handling
  Map<String, dynamic>? _lastHandResult;
  DateTime? _lastResultTime;
  
  // New variables for full hand capture 
  bool _isCapturingFullHand = false;
  int _stableFrameCount = 0;
  static const int _requiredStableFrames = 2; // Reduced from 3 for faster capture
  static const double _stabilityThreshold = 0.08; // Increased from 0.05 for more lenient detection
  List<Map<String, double>> _lastStableLandmarks = [];
  DateTime? _handFirstDetectedTime;
  static const Duration _maxWaitTime = Duration(seconds: 3); // Reduced from 5 seconds for faster capture
  
  // Variables for both hands capture
  bool _leftHandCaptured = false;
  bool _rightHandCaptured = false;
  Uint8List? _leftHandImage;
  Uint8List? _rightHandImage;
  String _currentHandType = 'left'; // 'left' or 'right'
  
  // Performance optimization variables
  DateTime? _lastProcessingTime;
  static const Duration _minProcessingInterval = Duration(milliseconds: 50); // Reduced from 100ms for faster response
  static const int _maxFrameQueueSize = 2; // Reduced queue size for less lag
  static const Duration _frameProcessingTimeout = Duration(seconds: 1); // Reduced timeout

  // Add these variables at the top of the class
  List<Map<String, double>>? _leftHandLandmarks;
  List<Map<String, double>>? _rightHandLandmarks;

  @override
  void initState() {
    super.initState();
    print('HandTrackingScreen: Initializing camera...');
    _initializeCamera();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showInstructionDialog());
    
    // Set up method channel listener for hand results
    platform.setMethodCallHandler(_handleMethodCall);
    
    // Start MediaPipe processing immediately after camera initialization
    Future.delayed(const Duration(seconds: 2), () {
      _testMediaPipeConnection();
      _startImmediateProcessing();
    });
  }

  Future<dynamic> _handleMethodCall(MethodCall call) async {
    switch (call.method) {
      case 'handResult':
        print('HandTrackingScreen: Received hand result from iOS');
        final result = Map<String, dynamic>.from(call.arguments);
        _lastHandResult = result;
        _lastResultTime = DateTime.now();
        
        // Process the result immediately
        _processHandResult(result);
        break;
      default:
        print('HandTrackingScreen: Unknown method call: ${call.method}');
    }
  }

  void _startImmediateProcessing() {
    print('HandTrackingScreen: Starting immediate MediaPipe processing...');
    if (_cameraController != null && _cameraController.value.isInitialized) {
      // Force start the stream if not already running
      if (!_isStreaming) {
        print('HandTrackingScreen: Forcing stream start...');
        _startCameraStream();
      }
      
      // Start processing frames immediately
      Future.delayed(const Duration(milliseconds: 100), () {
        _processNextFrame();
      });
    } else {
      print('HandTrackingScreen: Camera not ready for immediate processing');
    }
  }

  Future<void> _testMediaPipeConnection() async {
    try {
      print('HandTrackingScreen: Testing MediaPipe connection...');
      final result = await platform.invokeMethod('testConnection');
      print('HandTrackingScreen: MediaPipe test result: $result');
    } catch (e) {
      print('HandTrackingScreen: MediaPipe test failed: $e');
    }
  }

  void _testDetection() {
    print('HandTrackingScreen: Manual detection test triggered');
      setState(() {
      _debugInfo = 'Manual test triggered\n'
          'Hands detected: ${_hands.length}\n'
          'Streaming: $_isStreaming\n'
          'Processing: $_isProcessing\n'
          'Camera initialized: ${_cameraController?.value.isInitialized}\n'
          'Frame queue size: ${_frameQueue.length}\n'
          'Frame skip count: $_frameSkipCount';
    });
    
    // Trigger a test frame processing
    if (_frameQueue.isNotEmpty) {
      print('HandTrackingScreen: Processing test frame...');
      _processNextFrame();
    } else {
      print('HandTrackingScreen: No frames in queue for testing');
    }
    
    // Also test with a simple test image
    _testWithSimpleImage();
  }

  Future<void> _testWithSimpleImage() async {
    try {
      print('HandTrackingScreen: Testing with simple image...');
      // Create a simple test image (256x192 with some pattern)
      final testImage = Uint8List(256 * 192 * 4); // BGRA format
      for (int i = 0; i < testImage.length; i += 4) {
        testImage[i] = 128;     // Blue
        testImage[i + 1] = 128; // Green
        testImage[i + 2] = 128; // Red
        testImage[i + 3] = 255; // Alpha
      }
      
      final options = <String, dynamic>{
        'data': testImage,
        'width': 256,
        'height': 192,
        'landmarkIndices': null,
      };
      
      final result = await platform.invokeMethod('processFrame', options).timeout(const Duration(seconds: 5));
      print('HandTrackingScreen: Test image result: $result');
    } catch (e) {
      print('HandTrackingScreen: Test image failed: $e');
    }
  }

  Future<void> _initializeCamera() async {
    try {
      print('HandTrackingScreen: Setting up CameraController with ${widget.camera.name}');
      setState(() => _isControllerReinitializing = true);
    _cameraController = CameraController(
        widget.camera,
        ResolutionPreset.high,
      enableAudio: false,
        imageFormatGroup: Platform.isIOS ? ImageFormatGroup.bgra8888 : ImageFormatGroup.yuv420,
      );
      
      print('HandTrackingScreen: Initializing camera controller...');
      await _cameraController.initialize().timeout(const Duration(seconds: 15));
      print('HandTrackingScreen: Camera controller initialized successfully');
      
      if (!mounted) return;
      
      // Start with flash ON immediately for better hand detection
      print('HandTrackingScreen: Setting flash mode to TORCH...');
      await _cameraController.setFlashMode(FlashMode.torch);
      setState(() => _isFlashOn = true);
      
      if (_cameraController.value.isInitialized) {
        print('HandTrackingScreen: Camera is initialized, setting focus and exposure...');
        // Set auto focus and exposure for better image quality
        await _cameraController.setFocusMode(FocusMode.auto);
        await _cameraController.setExposureMode(ExposureMode.auto);
        
        // Set focus point to center for better hand detection
        await _cameraController.setFocusPoint(const Offset(0.5, 0.5));
        await _cameraController.setExposurePoint(const Offset(0.5, 0.5));
        
        print('HandTrackingScreen: Starting camera stream...');
        _startCameraStream();
      } else {
        print('HandTrackingScreen: Camera initialization failed - not initialized');
        throw Exception('Camera not initialized');
      }
      
      _minAvailableZoom = await _cameraController.getMinZoomLevel();
      _maxAvailableZoom = await _cameraController.getMaxZoomLevel();
      _currentZoomLevel = 1.0;
      await _cameraController.setZoomLevel(_currentZoomLevel);
      
      if (mounted) {
      setState(() {
          _isCameraInitialized = true;
          _isControllerReinitializing = false;
          _debugInfo = 'Camera initialized. Flash ON. Show your hand clearly.';
        });
        print('HandTrackingScreen: Camera setup complete');
      }
    } catch (e, stackTrace) {
      print('HandTrackingScreen: Error initializing camera: $e\nStack: $stackTrace');
      if (mounted) {
      setState(() {
          _isCameraInitialized = false;
          _isControllerReinitializing = false;
          _errorMessage = 'Camera init failed: $e';
          _debugInfo = 'Camera error: $e';
        });
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Camera init failed: $e')));
        await Future.delayed(const Duration(seconds: 2));
        if (!_isCameraInitialized) {
          print('HandTrackingScreen: Retrying camera initialization...');
          _initializeCamera();
        }
      }
    }
  }

  void _startCameraStream() {
    print('HandTrackingScreen: _startCameraStream called');
    print('HandTrackingScreen: _isStreaming: $_isStreaming');
    print('HandTrackingScreen: _isControllerReinitializing: $_isControllerReinitializing');
    print('HandTrackingScreen: _cameraController null: ${_cameraController == null}');
    print('HandTrackingScreen: camera initialized: ${_cameraController?.value.isInitialized}');
    print('HandTrackingScreen: mounted: $mounted');
    
    if (_isStreaming || _isControllerReinitializing || _cameraController == null || !_cameraController.value.isInitialized || !mounted) {
      print('HandTrackingScreen: Cannot start stream - conditions not met');
      return;
    }
    
    print('HandTrackingScreen: Starting high-res stream...');
    try {
      _cameraController.startImageStream((CameraImage image) {
        // Only log occasionally to reduce overhead
        if (_frameSkipCount % 20 == 0) { // Increased from 10 to reduce logging
          print('HandTrackingScreen: Received camera frame: ${image.width}x${image.height}');
        }
        
        // Limit queue size to prevent memory issues but allow more frames
        if (_frameQueue.length < _maxFrameQueueSize) {
          _frameQueue.add(image);
        }
        
        // Process frame immediately for better responsiveness
        if (!_isProcessing) {
          _processNextFrame();
        }
      }).then((_) {
        print('HandTrackingScreen: Camera stream started successfully');
        if (mounted) {
          setState(() {
            _isStreaming = true;
            _debugInfo = 'Camera streaming started. Show your hand clearly.';
          });
          
          // Start processing immediately after stream starts
          Future.delayed(const Duration(milliseconds: 100), () {
            _processNextFrame();
          });
        }
      }).catchError((e, stackTrace) {
        print('HandTrackingScreen: Stream start error: $e\nStack: $stackTrace');
        if (mounted) {
          setState(() {
            _isStreaming = false;
            _debugInfo = 'Stream error: $e';
          });
            }
          });
        } catch (e) {
      print('HandTrackingScreen: Exception starting stream: $e');
      if (mounted) {
          setState(() {
          _isStreaming = false;
          _debugInfo = 'Stream exception: $e';
        });
      }
    }
  }

  void _stopCameraStream() {
    if (!_isStreaming || !mounted || _cameraController == null || !_cameraController.value.isInitialized) return;
    print('HandTrackingScreen: Stopping stream...');
    _cameraController.stopImageStream().then((_) {
      if (mounted) setState(() => _isStreaming = false);
      _frameQueue.clear();
    }).catchError((e, stackTrace) {
      print('HandTrackingScreen: Stream stop error: $e\nStack: $stackTrace');
      if (mounted) setState(() => _debugInfo = 'Stop error: $e');
    });
  }

  Future<void> _processNextFrame() async {
    if (_isProcessing || _frameQueue.isEmpty) return;
    
    // Rate limiting to prevent lag but allow more frequent processing
    final now = DateTime.now();
    if (_lastProcessingTime != null && now.difference(_lastProcessingTime!) < _minProcessingInterval) {
      _isProcessing = false;
      return;
    }
    _lastProcessingTime = now;
    
    _isProcessing = true;
    
    print('HandTrackingScreen: Processing frame ${_frameSkipCount + 1}');
    
    // Process every 2nd frame for better responsiveness
    if (_frameSkipCount++ % (_frameSkipInterval + 1) != 0) {
      print('HandTrackingScreen: Skipping frame (processing every ${_frameSkipInterval + 1}th frame)');
      _isProcessing = false;
      return;
    }
    
    final image = _frameQueue.removeFirst();
    print('HandTrackingScreen: Processing frame with dimensions: ${image.width}x${image.height}');
    
    try {
      await _processImageStream(image);
    } catch (e) {
      print('HandTrackingScreen: Error processing frame: $e');
    }
    
    _isProcessing = false;
    
    // Continue processing immediately for better responsiveness
    if (_frameQueue.isNotEmpty) {
      Future.delayed(const Duration(milliseconds: 25), () => _processNextFrame());
    }
  }

  void _showInstructionDialog() {
    if (_dialogShown || !mounted) return;
    _dialogShown = true;
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        title: const Text("Both Hands Capture"),
        content: const Text("This app will capture both your left and right hands.\n\n📋 Instructions:\n\n1. Start with your LEFT hand\n2. Position your hand in the center guide\n3. Palm facing the camera\n4. Fingers spread naturally\n5. Keep hand stable until captured\n6. Then repeat with your RIGHT hand\n\nThe app will automatically extract each finger and save them with white backgrounds."),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _dialogShown = false;
            },
            child: const Text("Start"),
          ),
        ],
      ),
    );
  }

  Future<void> _processImageStream(CameraImage image) async {
    if (!mounted || _cameraController == null || !_cameraController.value.isInitialized) return;

    try {
      // Only log occasionally to reduce overhead
      if (_frameSkipCount % 20 == 0) { // Increased from 10 to reduce logging
        print('=== Processing frame: ${image.width}x${image.height} ===');
      }
      
      if (image.width <= 0 || image.height <= 0) throw Exception('Invalid frame dimensions');

      Uint8List combinedData;
      const targetWidth = 128; // Reduced from 160 for faster processing
      const targetHeight = 96; // Reduced from 120 for faster processing
      final expectedSize = targetWidth * targetHeight * (Platform.isIOS ? 4 : 3);

      if (Platform.isIOS) {
        final bgraImage = img.Image.fromBytes(width: image.width, height: image.height, bytes: image.planes[0].bytes.buffer, order: img.ChannelOrder.bgra);
        final enhancedImage = _enhanceImageContrast(bgraImage);
        final resizedImage = img.copyResize(enhancedImage, width: targetWidth, height: targetHeight);
        combinedData = resizedImage.getBytes(order: img.ChannelOrder.bgra);
        if (_frameSkipCount % 10 == 0) {
          print('iOS: Converted to BGRA, size: ${combinedData.length} bytes');
        }
      } else {
        combinedData = await platform.invokeMethod('convertYUV420ToRGB', {
          'yData': image.planes[0].bytes,
          'uData': image.planes[1].bytes,
          'vData': image.planes[2].bytes,
          'width': image.width,
          'height': image.height,
          'targetWidth': targetWidth,
          'targetHeight': targetHeight,
        });
        if (_frameSkipCount % 10 == 0) {
          print('Android: Converted to RGB, size: ${combinedData.length} bytes');
        }
      }

      if (combinedData.length != expectedSize) {
        print('ERROR: Expected size: $expectedSize, got: ${combinedData.length}');
        throw Exception('Invalid data size: expected $expectedSize, got ${combinedData.length}');
      }

      if (_frameSkipCount % 10 == 0) {
        print('Sending to MediaPipe...');
      }
      
      final options = <String, dynamic>{
        'data': combinedData,
        'width': targetWidth,
        'height': targetHeight,
        'landmarkIndices': null,
      };

      final startTime = DateTime.now();
      final result = await platform.invokeMethod('processFrame', options).timeout(_frameProcessingTimeout);
      final endTime = DateTime.now();
      final processingTime = endTime.difference(startTime).inMilliseconds;
      
      if (_frameSkipCount % 20 == 0) { // Increased from 10 to reduce logging
        print('MediaPipe processing time: ${processingTime}ms');
      }
      print('MediaPipe result: $result');

      if (result != null && result['success'] == true) {
        // For live stream, we just sent the frame for processing
        // Results will come back asynchronously
        if (_frameSkipCount % 20 == 0) {
          print('Frame sent for live stream processing');
        }
        
        // Use the last available result if we have one
        if (_lastHandResult != null && _lastResultTime != null) {
          final timeSinceLastResult = DateTime.now().difference(_lastResultTime!);
          if (timeSinceLastResult.inMilliseconds < 500) { // Use result if it's recent
            _processHandResult(_lastHandResult!);
          }
        }
      } else {
        print('MediaPipe failed or no result');
        print('Result: $result');
        if (mounted) setState(() => _errorMessage = 'No valid result: ${result?['error'] ?? 'Unknown'}');
      }
    } catch (e, stackTrace) {
      print('Processing error: $e');
      print('Stack trace: $stackTrace');
      if (mounted) setState(() => _errorMessage = 'Error: $e');
      _showErrorSnackBar('Processing error: $e');
    }
  }

  Future<void> _processHandResult(Map<String, dynamic> result) async {
    try {
      final allLandmarks = <Map<String, double>>[];
      final rawLandmarks = result['landmarks'] as List<dynamic>?;
      
      if (rawLandmarks != null && rawLandmarks.isNotEmpty) {
        if (_frameSkipCount % 20 == 0) {
          print('Found ${rawLandmarks.length} landmarks');
        }
        for (final e in rawLandmarks) {
          final map = Map<String, dynamic>.from(e as Map);
          allLandmarks.add({
            'x': (map['x'] as num? ?? 0.0).toDouble(),
            'y': (map['y'] as num? ?? 0.0).toDouble(),
            'z': (map['z'] as num? ?? 0.0).toDouble(),
          });
        }
      } else {
        if (_frameSkipCount % 20 == 0) {
          print('No landmarks found in result');
        }
      }
      
      final handednessList = (result['handedness'] as List?)?.map((e) => e.toString()).toList() ?? [];
      final confidences = (result['confidences'] as List?)?.map((e) => (e as num).toDouble()).toList() ?? [];
      
      if (_frameSkipCount % 20 == 0) {
        print('Handedness: $handednessList');
        print('Confidences: $confidences');
      }

      List<Map<String, dynamic>> hands = [];
      for (int i = 0; i < (allLandmarks?.length ?? 0); i += 21) {
        if (i ~/ 21 < (confidences?.length ?? 0)) {
          final landmarks = allLandmarks.sublist(i, min(i + 21, allLandmarks.length));
          hands.add({
            'landmarks': landmarks,
            'handedness': handednessList[i ~/ 21],
            'confidence': confidences[i ~/ 21],
          });
        }
      }

      if (_frameSkipCount % 20 == 0) {
        print('Processed ${hands.length} hands');
      }

      if (mounted) setState(() {
        _hands = hands;
        _errorMessage = null;
      });

      // Check for full hand capture conditions
      if (_hands.isNotEmpty && _hands[0]['confidence'] >= _confidenceThreshold) {
        if (_frameSkipCount % 20 == 0) {
          print('Hand detected with confidence: ${_hands[0]['confidence']}');
        }
        final landmarks = _hands[0]['landmarks'] as List<Map<String, double>>;
        final handName = _hands[0]['handedness'] ?? 'Unknown';
        
        // Debug landmark count
        print('Landmarks detected: ${landmarks.length}/21');
        if (landmarks.length == 21) {
          print('All 21 landmarks detected - finger boxes should be visible');
        }
        
        // Determine which hand we're looking for
        String targetHand = _currentHandType == 'left' ? 'Left' : 'Right';
        bool isCorrectHand = handName.toLowerCase().contains(targetHand.toLowerCase());
        
        if (!isCorrectHand) {
      setState(() {
            _debugInfo = '❌ Wrong hand detected\n'
                'Detected: $handName\n'
                'Required: $targetHand\n'
                'Please show your $targetHand hand';
      });
      return;
    }
        
        // Track when hand is first detected
        if (_handFirstDetectedTime == null) {
          _handFirstDetectedTime = DateTime.now();
          print('$targetHand hand first detected, starting timer...');
        }
        
        // Set focus to hand center for better image quality
        if (_stableFrameCount == 0) {
          final centerX = landmarks.map((l) => l['x'] ?? 0.0).reduce((a, b) => a + b) / landmarks.length;
          final centerY = landmarks.map((l) => l['y'] ?? 0.0).reduce((a, b) => a + b) / landmarks.length;
          
          // Set focus point to hand center
          _cameraController.setFocusPoint(Offset(centerX, centerY));
          _cameraController.setExposurePoint(Offset(centerX, centerY));
        }
        
        // Check if hand is stable
        if (_isHandStable(landmarks)) {
          _stableFrameCount++;
          print('$targetHand hand stable: $_stableFrameCount/$_requiredStableFrames');
          if (_stableFrameCount >= _requiredStableFrames && !_isCapturingFullHand) {
            print('Starting capture for $targetHand hand!');
            _isCapturingFullHand = true;
            await _captureFullHand();
          }
        } else {
          _stableFrameCount = 0;
          print('$targetHand hand not stable, resetting counter');
        }
        
        // Check timeout - capture even if not perfectly stable
        if (_handFirstDetectedTime != null && 
            DateTime.now().difference(_handFirstDetectedTime!) > _maxWaitTime && 
            !_isCapturingFullHand) {
          print('Timeout reached, capturing $targetHand hand anyway...');
          _isCapturingFullHand = true;
          await _captureFullHand();
        }

        // Update debug info with more details
        final avgZ = landmarks.map((l) => l['z'] ?? 0.0).reduce((a, b) => a + b) / landmarks.length;
        final confidence = _hands[0]['confidence'];
        
      setState(() {
          _debugInfo = '✅ $targetHand Hand Detected!\n'
              'Type: $handName\n'
              'Confidence: ${(confidence * 100).toStringAsFixed(1)}%\n'
              'Stable frames: $_stableFrameCount/$_requiredStableFrames\n'
              'Z-depth: ${avgZ.toStringAsFixed(2)}\n'
              'Landmarks: ${landmarks.length}/21\n'
              'Status: ${_isCapturingFullHand ? '📸 Capturing...' : '🔄 Stabilizing...'}';
        });
      } else {
        _stableFrameCount = 0;
        _isCapturingFullHand = false;
        _handFirstDetectedTime = null; // Reset timer when no hand detected
        if (_hands.isNotEmpty) {
          print('Hand detected but confidence too low: ${_hands[0]['confidence']} < $_confidenceThreshold');
          final handName = _hands[0]['handedness'] ?? 'Unknown';
          final confidence = _hands[0]['confidence'];
      setState(() {
            _debugInfo = '⚠️ Hand detected but low confidence\n'
                'Type: $handName\n'
                'Confidence: ${(confidence * 100).toStringAsFixed(1)}%\n'
                'Required: ${(_confidenceThreshold * 100).toStringAsFixed(1)}%\n'
                'Show your hand more clearly';
          });
        } else {
          setState(() {
            _debugInfo = '❌ No hand detected\n'
                'Show your $_currentHandType hand clearly in the center\n'
                'Make sure your hand is well-lit';
          });
        }
      }
    } catch (e) {
      print('Error processing hand result: $e');
    }
  }

  bool _isHandStable(List<Map<String, double>> currentLandmarks) {
    if (_lastStableLandmarks.isEmpty) {
      _lastStableLandmarks = List.from(currentLandmarks);
      return false;
    }

    if (currentLandmarks.length != _lastStableLandmarks.length) {
      _lastStableLandmarks = List.from(currentLandmarks);
      return false;
    }

    double totalMovement = 0.0;
    for (int i = 0; i < currentLandmarks.length; i++) {
      final current = currentLandmarks[i];
      final last = _lastStableLandmarks[i];
      
      final dx = (current['x'] ?? 0.0) - (last['x'] ?? 0.0);
      final dy = (current['y'] ?? 0.0) - (last['y'] ?? 0.0);
      final dz = (current['z'] ?? 0.0) - (last['z'] ?? 0.0);
      
      totalMovement += sqrt(dx * dx + dy * dy + dz * dz);
    }

    final avgMovement = totalMovement / currentLandmarks.length;
    _lastStableLandmarks = List.from(currentLandmarks);
    
    // More lenient stability check - allow more movement
    return avgMovement < _stabilityThreshold;
  }

  Future<void> _captureFullHand() async {
    try {
      if (_hands.isEmpty) {
        print('No hand detected for capture');
        return;
      }

      final hand = _hands[0];
      final handedness = hand['handedness'] as String;
      final landmarks = List<Map<String, double>>.from(hand['landmarks']);
      
      print('Capturing ${handedness.toLowerCase()} hand with ${landmarks.length} landmarks');
      
      // Store landmarks for this hand
      if (handedness.toLowerCase().contains('left')) {
        _leftHandLandmarks = landmarks;
        print('Stored left hand landmarks');
      } else if (handedness.toLowerCase().contains('right')) {
        _rightHandLandmarks = landmarks;
        print('Stored right hand landmarks');
      }

      print('Starting full hand capture for $_currentHandType hand...');
      
      // Flash is already ON, no need to turn it on
      
      // Set focus to center of hand for better quality
      if (_hands.isNotEmpty) {
        final landmarks = _hands[0]['landmarks'] as List<Map<String, double>>;
        final centerX = landmarks.map((l) => l['x'] ?? 0.0).reduce((a, b) => a + b) / landmarks.length;
        final centerY = landmarks.map((l) => l['y'] ?? 0.0).reduce((a, b) => a + b) / landmarks.length;
        
        await _cameraController.setFocusPoint(Offset(centerX, centerY));
        await _cameraController.setExposurePoint(Offset(centerY, centerY));
        await Future.delayed(const Duration(milliseconds: 100)); // Reduced delay for faster capture
      }
      
      // Capture high-resolution image
      final XFile imageFile = await _cameraController.takePicture();
      final imageBytes = await imageFile.readAsBytes();
      
      // Store the image based on hand type
      if (handedness.toLowerCase().contains('left')) {
        _leftHandImage = imageBytes;
        _leftHandCaptured = true;
        print('Left hand captured and stored');
    } else {
        _rightHandImage = imageBytes;
        _rightHandCaptured = true;
        print('Right hand captured and stored');
      }
      
      // Check if both hands are captured
      if (_leftHandCaptured && _rightHandCaptured) {
        print('Both hands captured! Processing fingers...');
        await _processBothHands();
      } else {
        // Switch to next hand
        _currentHandType = _currentHandType == 'left' ? 'right' : 'left';
        _stableFrameCount = 0;
        _handFirstDetectedTime = null;
        _isCapturingFullHand = false;
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('$_currentHandType hand captured! Now show your ${_currentHandType == 'left' ? 'left' : 'right'} hand'),
              backgroundColor: Colors.green
            )
          );
        }
      }
      
    } catch (e) {
      print('Error capturing full hand: $e');
    }
  }

  bool _checkFullHandQuality(img.Image image) {
    print('=== Checking image quality ===');
    print('Image dimensions: ${image.width}x${image.height}');
    
    // If we have a hand detected, accept the image regardless of quality
    if (_hands.isNotEmpty) {
      print('Hand detected - accepting image regardless of quality');
      return true;
    }
    
    // Check if hand covers a reasonable portion of the image
    final handRegion = _getHandBoundingBox();
    if (handRegion != null) {
      final area = (handRegion['width'] ?? 0) * (handRegion['height'] ?? 0);
      final imageArea = image.width * image.height;
      final coverage = area / imageArea;
      
      print('Hand region: $handRegion');
      print('Hand coverage: ${(coverage * 100).toStringAsFixed(1)}%');
      
      // Hand should cover at least 5% of the image (very lenient)
      if (coverage < 0.05) {
        print('Hand coverage too small: ${(coverage * 100).toStringAsFixed(1)}%');
        return false;
      }
    } else {
      print('No hand region found, skipping coverage check');
    }
    
    // Check image sharpness and contrast
    final isSharp = _checkImageSharpness(image);
    final hasContrast = _checkImageContrast(image);
    
    print('Sharpness check: $isSharp');
    print('Contrast check: $hasContrast');
    
    // Accept if either check passes
    return isSharp || hasContrast;
  }

  Map<String, int>? _getHandBoundingBox() {
    if (_hands.isEmpty) return null;
    
    final landmarks = _hands[0]['landmarks'] as List<Map<String, double>>;
    if (landmarks.isEmpty) return null;
    
    double minX = 1.0, maxX = 0.0, minY = 1.0, maxY = 0.0;
    
    for (final landmark in landmarks) {
      final x = landmark['x'] ?? 0.0;
      final y = landmark['y'] ?? 0.0;
      
      minX = min(minX, x);
      maxX = max(maxX, x);
      minY = min(minY, y);
      maxY = max(maxY, y);
    }
    
    return {
      'x': (minX * 1000).round(),
      'y': (minY * 1000).round(),
      'width': ((maxX - minX) * 1000).round(),
      'height': ((maxY - minY) * 1000).round(),
    };
  }

  // _getFingerBoundingBoxes method removed - no bounding boxes needed in camera UI

  bool _checkImageSharpness(img.Image image) {
    // Simple edge detection for sharpness
    double edgeSum = 0.0;
    int edgeCount = 0;
    
    for (int y = 1; y < image.height - 1; y += 8) { // Increased step for faster processing
      for (int x = 1; x < image.width - 1; x += 8) { // Increased step for faster processing
        final pixel = image.getPixelSafe(x, y);
        final pixelRight = image.getPixelSafe(x + 1, y);
        final pixelDown = image.getPixelSafe(x, y + 1);
        
        final gradient = sqrt(
          pow(pixel.r - pixelRight.r, 2) + 
          pow(pixel.g - pixelRight.g, 2) + 
          pow(pixel.b - pixelRight.b, 2) +
          pow(pixel.r - pixelDown.r, 2) + 
          pow(pixel.g - pixelDown.g, 2) + 
          pow(pixel.b - pixelDown.b, 2)
        );
        
        edgeSum += gradient;
        edgeCount++;
      }
    }
    
    final avgSharpness = edgeCount > 0 ? edgeSum / edgeCount : 0.0;
    print('Image sharpness: $avgSharpness');
    return avgSharpness > 3.0; // Much more lenient - reduced from 8.0
  }

  bool _checkImageContrast(img.Image image) {
    // Calculate standard deviation of luminance
    double sum = 0.0, sumSq = 0.0;
    int count = 0;
    
    for (int y = 0; y < image.height; y += 8) { // Increased step for faster processing
      for (int x = 0; x < image.width; x += 8) { // Increased step for faster processing
        final pixel = image.getPixelSafe(x, y);
        final luminance = 0.299 * pixel.r + 0.587 * pixel.g + 0.114 * pixel.b;
        sum += luminance;
        sumSq += luminance * luminance;
        count++;
      }
    }
    
    if (count == 0) return false;
    
    final mean = sum / count;
    final variance = (sumSq / count) - (mean * mean);
    final stddev = sqrt(variance);
    
    print('Image contrast (stddev): $stddev');
    return stddev > 8.0; // Much more lenient - reduced from 15.0
  }

  Future<bool> _sendFullHandToServer(Uint8List imageBytes) async {
    const maxRetries = 3;
    for (int attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        final url = Uri.parse('${AppConfig.baseApiUrl}/upload-full-hand/');
        final request = http.MultipartRequest('POST', url);
        request.fields['finger_name'] = 'full_hand';
        request.files.add(http.MultipartFile.fromBytes('images', imageBytes, filename: 'full_hand.jpg'));
        
        final response = await request.send().timeout(const Duration(seconds: 10));
        final responseBody = await response.stream.bytesToString();
        final success = response.statusCode == 200 && responseBody.contains('success');
        
        if (success) {
          print('Full hand image sent successfully');
          print('Response: $responseBody');
        } else {
          print('Failed to send full hand image, attempt ${attempt + 1}');
          print('Response: $responseBody');
        }
        
        return success;
      } catch (e) {
        print('Send error for full hand, attempt $attempt: $e');
        if (attempt == maxRetries) return false;
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }
    return false;
  }

  void _showCompletionDialog() {
    if (_dialogShown || !mounted) return;
    _dialogShown = true;
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        title: const Text("Both Hands Processed"),
        content: const Text("Both left and right hands have been captured and processed. All 10 fingers have been extracted with white backgrounds and saved to the server."),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _dialogShown = false;
              Navigator.pop(context); // Return to previous screen
            },
            child: const Text("Done"),
          ),
        ],
      ),
    );
  }

  void _showErrorSnackBar(String message) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message), backgroundColor: Colors.red));
  }

  img.Image _enhanceImageContrast(img.Image image) {
    return img.adjustColor(image, contrast: 1.2, brightness: 1.0);
  }

  Future<void> _onTapToFocus(TapDownDetails details) async {
    if (_cameraController != null && _cameraController.value.isInitialized && !_isFocusing && mounted) {
      final renderBox = context.findRenderObject() as RenderBox?;
      if (renderBox != null) {
        final localPosition = renderBox.globalToLocal(details.globalPosition);
        final x = localPosition.dx / renderBox.size.width;
        final y = localPosition.dy / renderBox.size.height;
        setState(() => _isFocusing = true);
        try {
          await _cameraController.setFocusPoint(Offset(x, y));
          await _cameraController.setExposurePoint(Offset(x, y));
          await Future.delayed(const Duration(milliseconds: 500));
          if (mounted) {
            await _cameraController.setFocusMode(FocusMode.auto);
            await _cameraController.setExposureMode(ExposureMode.auto);
            setState(() => _isFocusing = false);
          }
        } catch (e) {
          print('Tap focus error: $e');
          if (mounted) setState(() => _isFocusing = false);
        }
      }
    }
  }

  Future<void> _toggleFlash() async {
    if (_cameraController == null || !_cameraController.value.isInitialized || !mounted) return;
    _isFlashOn = !_isFlashOn;
    try {
      await _cameraController.setFlashMode(_isFlashOn ? FlashMode.torch : FlashMode.off);
      if (mounted) setState(() {});
    } catch (e) {
      print('Toggle flash error: $e');
      if (mounted) setState(() {});
    }
  }

  Future<void> _adjustZoom(bool isZoomIn) async {
    if (_cameraController != null && _cameraController.value.isInitialized && mounted) {
      setState(() => _currentZoomLevel = (isZoomIn ? _currentZoomLevel + 0.1 : _currentZoomLevel - 0.1).clamp(_minAvailableZoom, _maxAvailableZoom));
      try {
        await _cameraController.setZoomLevel(_currentZoomLevel);
      } catch (e) {
        print('Adjust zoom error: $e');
        if (mounted) setState(() {});
      }
    }
  }

  void _toggleStream() {
    if (_cameraController == null || !_cameraController.value.isInitialized || !mounted) return;
    if (_isStreaming) {
      _stopCameraStream();
    } else {
      _startCameraStream();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text('Full Hand Capture', style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.grey[900],
        actions: [
          // Removed play/stop button - camera runs automatically
          IconButton(
            icon: Icon(_isFlashOn ? Icons.flash_on : Icons.flash_off, color: Colors.yellowAccent), 
            onPressed: _toggleFlash
          ),
          // Test button for debugging
          IconButton(
            icon: const Icon(Icons.bug_report, color: Colors.white),
            onPressed: _testDetection,
          ),
          // Manual stream start button
          IconButton(
            icon: Icon(_isStreaming ? Icons.stop : Icons.play_arrow, color: Colors.white),
            onPressed: _toggleStream,
          ),
        ],
      ),
      body: SafeArea(
        child: (_isCameraInitialized && _cameraController.value.isInitialized && !_isControllerReinitializing)
            ? GestureDetector(
                onTapDown: _onTapToFocus,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    CameraPreview(_cameraController),
                    if (_errorMessage != null)
                      Center(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red, fontSize: 16))),
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text('Show your complete hand', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 10),
                          Text(
                            _isCapturingFullHand ? 'Capturing...' : 
                            (_hands.isEmpty ? 'Position your $_currentHandType hand' : 'Stabilizing $_currentHandType hand...'),
                            style: const TextStyle(color: Colors.white, fontSize: 16),
                            textAlign: TextAlign.center
                          ),
                          if (_leftHandCaptured || _rightHandCaptured)
                            Padding(
                              padding: const EdgeInsets.only(top: 10),
                              child: Text(
                                _leftHandCaptured && _rightHandCaptured 
                                  ? 'Both hands captured! Processing fingers...'
                                  : '${_leftHandCaptured ? "Left" : "Right"} hand captured. Show your ${_currentHandType == "left" ? "right" : "left"} hand.',
                                style: const TextStyle(color: Colors.green, fontSize: 14, fontWeight: FontWeight.bold),
                                textAlign: TextAlign.center,
                              ),
                            ),
                        ],
                      ),
          ),
          Positioned(
                      top: 16, 
                      left: 16, 
                      right: 16, 
                      child: Container(
                        padding: const EdgeInsets.all(12), 
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.8),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.white.withOpacity(0.3), width: 1),
                        ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                            Row(
                              children: [
                                Icon(
                                  _hands.isNotEmpty ? Icons.handshake : Icons.handshake_outlined,
                                  color: _hands.isNotEmpty ? Colors.green : Colors.grey,
                                  size: 20,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  _hands.isNotEmpty ? 'Hand Detected' : 'No Hand',
                                  style: TextStyle(
                                    color: _hands.isNotEmpty ? Colors.green : Colors.grey,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                  ),
                                ),
                                const SizedBox(width: 16),
                                // MediaPipe processing indicator
                                Container(
                                  width: 8,
                                  height: 8,
                                  decoration: BoxDecoration(
                                    color: _isProcessing ? Colors.orange : Colors.grey,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 4),
                Text(
                                  _isProcessing ? 'Processing' : 'Ready',
                                  style: TextStyle(
                                    color: _isProcessing ? Colors.orange : Colors.grey,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                  Text(
                              _debugInfo,
                              style: const TextStyle(
              color: Colors.white,
                                fontSize: 12,
                                height: 1.3,
            ),
          ),
        ],
      ),
                      )
                    ),
                    Positioned(
                      bottom: 20, 
                      left: 20, 
                      right: 20, 
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween, 
        children: [
                          FloatingActionButton(
                            heroTag: 'zoom_in', 
                            backgroundColor: Colors.black87, 
                            onPressed: () => _adjustZoom(true), 
                            child: const Icon(Icons.zoom_in, color: Colors.white)
                          ),
                          FloatingActionButton(
                            heroTag: 'zoom_out', 
                            backgroundColor: Colors.black87, 
                            onPressed: () => _adjustZoom(false), 
                            child: const Icon(Icons.zoom_out, color: Colors.white)
                          ),
                          FloatingActionButton(
                            heroTag: 'flash',
                            backgroundColor: Colors.black87,
                            onPressed: _toggleFlash,
                            child: Icon(
                              _isFlashOn ? Icons.flash_on : Icons.flash_off,
                              color: Colors.yellowAccent,
                            ),
                          ),
                        ]
                      )
                    ),
          CustomPaint(
                      painter: HandLandmarkPainter(_hands, _cameraController.value.previewSize, RegistrationStep.showLeftHand, _confidenceThreshold)
                    ),
                    
                    // Finger bounding boxes - REMOVED for cleaner UI
                    // if (_hands.isNotEmpty && _hands[0]['landmarks'].length == 21)
                    //   Builder(
                    //     builder: (context) {
                    //       final fingerBoxes = _getFingerBoundingBoxes();
                    //       print('Finger boxes calculated: ${fingerBoxes?.length ?? 0} boxes');
                    //       if (fingerBoxes != null) {
                    //         fingerBoxes.forEach((finger, box) {
                    //           print('$finger: x=${box['x']}, y=${box['y']}, w=${box['width']}, h=${box['height']}');
                    //         });
                    //       }
                    //       return CustomPaint(
                    //         painter: FingerBoundingBoxPainter(fingerBoxes, _cameraController.value.previewSize),
                    //         size: Size.infinite,
                    //       );
                    //     },
                    //   ),
                    
                    // Hand positioning outline guide
                    if (_hands.isEmpty || _hands[0]['confidence'] < _confidenceThreshold)
                      Center(
                        child: Container(
                          width: 200,
                          height: 250,
                          decoration: BoxDecoration(
                            border: Border.all(
                              color: Colors.white.withOpacity(0.6),
                              width: 2,
                              style: BorderStyle.solid,
                            ),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Stack(
                            children: [
                              // Hand outline
          Positioned(
                                top: 20,
                                left: 20,
                                right: 20,
            bottom: 20,
                                child: CustomPaint(
                                  painter: HandOutlinePainter(_currentHandType),
                                  size: Size.infinite,
                                ),
                              ),
                              // Position text
                              Positioned(
                                bottom: 10,
                                left: 0,
                                right: 0,
                                child: Text(
                                  'Position your ${_currentHandType} hand here',
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.8),
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    
                    // Visual indicator for stable hand
                    if (_stableFrameCount >= _requiredStableFrames && !_isCapturingFullHand)
                      Positioned.fill(
                        child: Container(
                          decoration: BoxDecoration(
                            border: Border.all(
                              color: Colors.green,
                              width: 3,
                            ),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Center(
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              decoration: BoxDecoration(
                                color: Colors.green.withOpacity(0.9),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: const Text(
                                'HAND STABLE - READY TO CAPTURE',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    
                    // Hand positioning guide
                    Positioned(
                      top: 100,
            left: 20,
                      right: 20,
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.8),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.white.withOpacity(0.3)),
                        ),
            child: Column(
              children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  _currentHandType == 'left' ? Icons.pan_tool : Icons.pan_tool_alt,
                                  color: Colors.blue,
                                  size: 24,
                                ),
                                const SizedBox(width: 8),
                Text(
                                  'Show your ${_currentHandType.toUpperCase()} hand',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                  Text(
                              _currentHandType == 'left' 
                                ? '• Place your LEFT hand in the center\n• Palm facing the camera\n• Fingers spread naturally\n• Keep hand stable'
                                : '• Place your RIGHT hand in the center\n• Palm facing the camera\n• Fingers spread naturally\n• Keep hand stable',
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 14,
                                height: 1.4,
                              ),
                              textAlign: TextAlign.center,
                  ),
              ],
            ),
                      ),
                    ),
                    
                    // Progress indicator
                    if (_leftHandCaptured || _rightHandCaptured)
                      Positioned(
                        bottom: 100,
                        left: 20,
                        right: 20,
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.8),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.green.withOpacity(0.5)),
                          ),
                          child: Column(
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'Left Hand',
                                    style: TextStyle(
                                      color: _leftHandCaptured ? Colors.green : Colors.grey,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  Icon(
                                    _leftHandCaptured ? Icons.check_circle : Icons.circle_outlined,
                                    color: _leftHandCaptured ? Colors.green : Colors.grey,
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'Right Hand',
                                    style: TextStyle(
                                      color: _rightHandCaptured ? Colors.green : Colors.grey,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  Icon(
                                    _rightHandCaptured ? Icons.check_circle : Icons.circle_outlined,
                                    color: _rightHandCaptured ? Colors.green : Colors.grey,
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              )
            : Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center, 
                  children: [
                    const CircularProgressIndicator(), 
                    const SizedBox(height: 16), 
                    Text(_errorMessage ?? 'Initializing...', style: const TextStyle(color: Colors.white))
                  ]
                )
              ),
      ),
    );
  }

  Future<void> _processBothHands() async {
    try {
      print('Processing both hands for finger extraction...');
      
      if (_leftHandImage == null || _rightHandImage == null) {
        print('Error: Missing hand images');
        return;
      }
      
      if (_leftHandLandmarks == null || _rightHandLandmarks == null) {
        print('Error: Missing hand landmarks');
        return;
      }
      
      print('Left hand landmarks: ${_leftHandLandmarks!.length}');
      print('Right hand landmarks: ${_rightHandLandmarks!.length}');
      
      // Process left hand fingers with stored landmarks
      final leftHandImage = img.decodeImage(_leftHandImage!);
      if (leftHandImage != null) {
        await _extractFingersFromHand(leftHandImage, 'left', _leftHandLandmarks);
      }
      
      // Process right hand fingers with stored landmarks
      final rightHandImage = img.decodeImage(_rightHandImage!);
      if (rightHandImage != null) {
        await _extractFingersFromHand(rightHandImage, 'right', _rightHandLandmarks);
      }
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Both hands processed! Finger extraction complete.'),
            backgroundColor: Colors.green
          )
        );
        _showCompletionDialog();
      }
      
    } catch (e) {
      print('Error processing both hands: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error processing hands: $e'),
            backgroundColor: Colors.red
          )
        );
      }
    }
  }
  
  Future<void> _extractFingersFromHand(img.Image handImage, String handType, List<Map<String, double>>? storedLandmarks) async {
    try {
      print('Extracting fingers from $handType hand...');
      
      // Use stored landmarks or current landmarks
      List<Map<String, double>>? handLandmarks = storedLandmarks;
      if (handLandmarks == null && _hands.isNotEmpty) {
        handLandmarks = List<Map<String, double>>.from(_hands[0]['landmarks']);
      }
      
      if (handLandmarks == null || handLandmarks.length < 21) {
        print('Not enough landmarks for precise finger extraction');
        return;
      }

      // Define finger regions with proper landmark indices
      // MediaPipe hand landmarks: 0-20 (21 total)
      // For left hand, process in this order: thumb(1-4), index(5-8), middle(9-12), ring(13-16), pinky(17-20)
      // For right hand, same order
      final fingerRegions = [
        {
          'tip': 4,           // Thumb tip
          'dip': 3,           // Distal interphalangeal joint
          'pip': 2,           // Proximal interphalangeal joint
          'mcp': 1,           // Metacarpophalangeal joint
          'name': 'thumb',    // Will be prefixed with handType
        },
        {
          'tip': 8,           // Index fingertip
          'dip': 7,           // Distal interphalangeal joint
          'pip': 6,           // Proximal interphalangeal joint
          'mcp': 5,           // Metacarpophalangeal joint
          'name': 'index',
        },
        {
          'tip': 12,          // Middle fingertip
          'dip': 11,          // Distal interphalangeal joint
          'pip': 10,          // Proximal interphalangeal joint
          'mcp': 9,           // Metacarpophalangeal joint
          'name': 'middle',
        },
        {
          'tip': 16,          // Ring fingertip
          'dip': 15,          // Distal interphalangeal joint
          'pip': 14,          // Proximal interphalangeal joint
          'mcp': 13,          // Metacarpophalangeal joint
          'name': 'ring',
        },
        {
          'tip': 20,          // Pinky fingertip
          'dip': 19,          // Distal interphalangeal joint
          'pip': 18,          // Proximal interphalangeal joint
          'mcp': 17,          // Metacarpophalangeal joint
          'name': 'pinky',
        },
      ];

      // For left hand, we need to process in reverse order to match MediaPipe's landmark ordering
      final processedRegions = handType == 'left' ? fingerRegions.reversed.toList() : fingerRegions;
      
      // Process fingers in correct order
      for (final region in processedRegions) {
        final fingerName = region['name'] as String;
        
        // Get all landmarks for this finger
        final tipIndex = region['tip'] as int;
        final dipIndex = region['dip'] as int;
        final pipIndex = region['pip'] as int;
        final mcpIndex = region['mcp'] as int;
        
        print('Processing ${handType}_$fingerName using landmarks: tip=$tipIndex, dip=$dipIndex, pip=$pipIndex, mcp=$mcpIndex');
        
        // Get landmark coordinates
        final tipLandmark = handLandmarks[tipIndex];
        final dipLandmark = handLandmarks[dipIndex];
        final pipLandmark = handLandmarks[pipIndex];
        final mcpLandmark = handLandmarks[mcpIndex];
        
        // Calculate finger direction vector from base to tip
        final dirX = tipLandmark['x']! - mcpLandmark['x']!;
        final dirY = tipLandmark['y']! - mcpLandmark['y']!;
        final fingerLength = sqrt(dirX * dirX + dirY * dirY);
        
        // Calculate perpendicular vector for width
        final perpX = -dirY / fingerLength;
        final perpY = dirX / fingerLength;
        
        // Calculate finger width at each joint
        final dipWidth = _distanceBetweenPoints(dipLandmark, pipLandmark);
        final pipWidth = _distanceBetweenPoints(pipLandmark, mcpLandmark);
        final maxWidth = max(dipWidth, pipWidth);
        
        // Calculate crop box with padding
        final widthPadding = maxWidth * 1.0; // 100% of finger width
        final heightPadding = maxWidth * 0.8; // 80% of finger width for height
        
        // Calculate bounding box around fingertip region
        double minX = double.infinity;
        double maxX = double.negativeInfinity;
        double minY = double.infinity;
        double maxY = double.negativeInfinity;
        
        // Use tip and DIP joint for bounding box
        final points = [tipLandmark, dipLandmark];
        for (final point in points) {
          final x = point['x'] ?? 0.0;
          final y = point['y'] ?? 0.0;
          minX = min(minX, x);
          maxX = max(maxX, x);
          minY = min(minY, y);
          maxY = max(maxY, y);
        }
        
        // Add padding
        minX -= widthPadding;
        maxX += widthPadding;
        minY -= heightPadding;
        maxY += heightPadding;
        
        // Clamp to image bounds
        minX = minX.clamp(0.0, 1.0);
        maxX = maxX.clamp(0.0, 1.0);
        minY = minY.clamp(0.0, 1.0);
        maxY = maxY.clamp(0.0, 1.0);
        
        // Convert to image coordinates
        final cropX = (minX * handImage.width).round();
        final cropY = (minY * handImage.height).round();
        final cropWidth = ((maxX - minX) * handImage.width).round();
        final cropHeight = ((maxY - minY) * handImage.height).round();
        
        print('Cropping ${handType}_$fingerName: x=$cropX, y=$cropY, w=$cropWidth, h=$cropHeight');
        
        // Ensure valid crop dimensions
        if (cropWidth <= 0 || cropHeight <= 0) {
          print('Invalid crop dimensions for ${handType}_$fingerName, skipping');
          continue;
        }
        
        // Adjust crop coordinates to stay within image bounds
        final adjustedX = cropX.clamp(0, handImage.width - 1);
        final adjustedY = cropY.clamp(0, handImage.height - 1);
        final adjustedWidth = cropWidth.clamp(1, handImage.width - adjustedX);
        final adjustedHeight = cropHeight.clamp(1, handImage.height - adjustedY);
        
        // Crop the finger region
        final croppedFinger = img.copyCrop(
          handImage,
          x: adjustedX,
          y: adjustedY,
          width: adjustedWidth,
          height: adjustedHeight
        );
        
        // Create white background
        final whiteBackground = img.Image(width: adjustedWidth, height: adjustedHeight);
        for (int y = 0; y < adjustedHeight; y++) {
          for (int x = 0; x < adjustedWidth; x++) {
            whiteBackground.setPixelRgb(x, y, 255, 255, 255);
          }
        }
        
        // Composite finger onto white background
        img.compositeImage(whiteBackground, croppedFinger);
        
        // Generate filename with proper naming convention
        final fingerInfo = '${handType}_$fingerName';
        
        // Convert to PNG for better quality
        final fingerImageBytes = img.encodePng(whiteBackground);
        
        // Send to server
        await _sendFingerToServer(fingerImageBytes, fingerInfo);
        
        print('Processed ${handType}_$fingerName');
      }
      
    } catch (e) {
      print('Error extracting fingers from $handType hand: $e');
    }
  }
  
  double _distanceBetweenPoints(Map<String, double> p1, Map<String, double> p2) {
    final dx = (p1['x'] ?? 0.0) - (p2['x'] ?? 0.0);
    final dy = (p1['y'] ?? 0.0) - (p2['y'] ?? 0.0);
    return sqrt(dx * dx + dy * dy);
  }
  
  Future<bool> _sendFingerToServer(Uint8List imageBytes, String fingerInfo) async {
    const maxRetries = 3;
    for (int attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        final url = Uri.parse('${AppConfig.baseApiUrl}/upload-finger/');
        final request = http.MultipartRequest('POST', url);
        request.fields['finger_info'] = fingerInfo;
        request.files.add(http.MultipartFile.fromBytes('images', imageBytes, filename: '$fingerInfo.png'));
        
        final response = await request.send().timeout(const Duration(seconds: 10));
        final responseBody = await response.stream.bytesToString();
        final success = response.statusCode == 200 && responseBody.contains('success');
        
        if (success) {
          print('Finger image sent successfully: $fingerInfo');
        } else {
          print('Failed to send finger image: $fingerInfo');
        }
        
        return success;
      } catch (e) {
        print('Send error for finger $fingerInfo, attempt $attempt: $e');
        if (attempt == maxRetries) return false;
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }
    return false;
  }

  @override
  void dispose() {
    print('HandTrackingScreen: Disposing...');
    
    // Remove method channel handler
    platform.setMethodCallHandler(null);
    
    // Stop stream first
    if (_isStreaming) {
      print('HandTrackingScreen: Stopping stream...');
      _cameraController.stopImageStream();
      _isStreaming = false;
    }
    
    // Turn off flash and dispose camera
    if (_cameraController != null) {
      try {
        if (_cameraController.value.isInitialized) {
          _cameraController.setFlashMode(FlashMode.off).then((_) {
            _cameraController.dispose();
          });
        } else {
          _cameraController.dispose();
        }
      } catch (e, stackTrace) {
        print('Dispose error: $e\nStack: $stackTrace');
      }
    }
    
    super.dispose();
  }
}

extension StringExtension on String {
  String capitalize() => "${this[0].toUpperCase()}${substring(1).toLowerCase()}";
}

class HandOutlinePainter extends CustomPainter {
  final String handType;
  
  HandOutlinePainter(this.handType);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0
      ..color = Colors.white.withOpacity(0.7);
    
    // Draw a simple hand outline
    final path = Path();
    
    if (handType == 'left') {
      // Left hand outline (palm facing right)
      path.moveTo(size.width * 0.3, size.height * 0.2); // Thumb base
      path.lineTo(size.width * 0.2, size.height * 0.3);
      path.lineTo(size.width * 0.15, size.height * 0.4);
      path.lineTo(size.width * 0.2, size.height * 0.5);
      path.lineTo(size.width * 0.3, size.height * 0.6);
      
      // Palm
      path.moveTo(size.width * 0.3, size.height * 0.2);
      path.lineTo(size.width * 0.7, size.height * 0.2);
      path.lineTo(size.width * 0.8, size.height * 0.4);
      path.lineTo(size.width * 0.7, size.height * 0.8);
      path.lineTo(size.width * 0.3, size.height * 0.8);
      path.close();
      
      // Fingers
      path.moveTo(size.width * 0.4, size.height * 0.2);
      path.lineTo(size.width * 0.4, size.height * 0.1);
      path.moveTo(size.width * 0.5, size.height * 0.2);
      path.lineTo(size.width * 0.5, size.height * 0.1);
      path.moveTo(size.width * 0.6, size.height * 0.2);
      path.lineTo(size.width * 0.6, size.height * 0.1);
      path.moveTo(size.width * 0.7, size.height * 0.2);
      path.lineTo(size.width * 0.7, size.height * 0.1);
    } else {
      // Right hand outline (palm facing left)
      path.moveTo(size.width * 0.7, size.height * 0.2); // Thumb base
      path.lineTo(size.width * 0.8, size.height * 0.3);
      path.lineTo(size.width * 0.85, size.height * 0.4);
      path.lineTo(size.width * 0.8, size.height * 0.5);
      path.lineTo(size.width * 0.7, size.height * 0.6);
      
      // Palm
      path.moveTo(size.width * 0.7, size.height * 0.2);
      path.lineTo(size.width * 0.3, size.height * 0.2);
      path.lineTo(size.width * 0.2, size.height * 0.4);
      path.lineTo(size.width * 0.3, size.height * 0.8);
      path.lineTo(size.width * 0.7, size.height * 0.8);
      path.close();
      
      // Fingers
      path.moveTo(size.width * 0.6, size.height * 0.2);
      path.lineTo(size.width * 0.6, size.height * 0.1);
      path.moveTo(size.width * 0.5, size.height * 0.2);
      path.lineTo(size.width * 0.5, size.height * 0.1);
      path.moveTo(size.width * 0.4, size.height * 0.2);
      path.lineTo(size.width * 0.4, size.height * 0.1);
      path.moveTo(size.width * 0.3, size.height * 0.2);
      path.lineTo(size.width * 0.3, size.height * 0.1);
    }
    
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(HandOutlinePainter oldDelegate) {
    return oldDelegate.handType != handType;
  }
}