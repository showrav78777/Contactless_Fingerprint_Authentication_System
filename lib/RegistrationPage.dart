// import 'package:camera/camera.dart';
// import 'package:flutter/material.dart';
// import 'package:http/http.dart' as http;
// import 'package:path_provider/path_provider.dart';

// class RegistrationPage extends StatefulWidget {
//   const RegistrationPage({super.key});

//   @override
//   _RegistrationPageState createState() => _RegistrationPageState();
// }

// class _RegistrationPageState extends State<RegistrationPage> {
//   late CameraController _cameraController;
//   late List<CameraDescription> _cameras;
//   bool _isCameraInitialized = false;
//   int _imageCount = 0;

//   final List<String> _captureOrder = [
//     'Left Thumb',
//     'Left Four Fingers',
//     'Right Thumb',
//     'Right Four Fingers'
//   ];
//   final List<String> _savedFilePaths = [];
//   bool _isFlashOn = false;

//   @override
//   void initState() {
//     super.initState();
//     _initializeCamera();
//   }

//   Future<void> _initializeCamera() async {
//     try {
//       _cameras = await availableCameras();
//       _cameraController = CameraController(
//         _cameras.first,
//         ResolutionPreset.high,
//         enableAudio: false,
//       );
//       await _cameraController.initialize();
//       setState(() {
//         _isCameraInitialized = true;
//       });
//     } catch (e) {
//       print('Error initializing camera: $e');
//     }
//   }

//   Future<void> _captureImage(String capturePhase) async {
//     if (!_cameraController.value.isInitialized) {
//       print('Camera is not initialized');
//       return;
//     }

//     try {
//       // Capture the picture
//       XFile image = await _cameraController.takePicture();

//       // Get the application documents directory
//       final directory = await getApplicationDocumentsDirectory();
//       final String newPath = '${directory.path}/$capturePhase.jpg';
//       await image.saveTo(newPath);

//       // Store the file paths for future reference
//       _savedFilePaths.add(newPath);

//       print('Saved $capturePhase image to: $newPath');

//       // Now upload the image to the server
//       await _uploadImageToServer(newPath, capturePhase);
//     } catch (e) {
//       print('Error capturing image: $e');
//     }
//   }

//   Future<void> _uploadImageToServer(
//       String filePath, String capturePhase) async {
//     try {
//       // Create a multipart request
//       var request = http.MultipartRequest(
//         'POST',
//         Uri.parse(
//             'http://your-backend-server.com/upload'), // Replace with your backend API
//       );

//       // Attach the image file and the phase name
//       request.files.add(await http.MultipartFile.fromPath('file', filePath));
//       request.fields['capturePhase'] = capturePhase;

//       // Send the request
//       var response = await request.send();

//       if (response.statusCode == 200) {
//         print('Image uploaded successfully.');
//       } else {
//         print('Failed to upload image: ${response.statusCode}');
//       }
//     } catch (e) {
//       print('Error uploading image: $e');
//     }
//   }

//   @override
//   void dispose() {
//     _cameraController.dispose();
//     super.dispose();
//   }

//   Widget _buildArcOverlay() {
//     return CustomPaint(
//       painter: ArcPainter(), // Create an arc-shaped overlay for guidance
//     );
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(
//         title: const Text('Capture Fingerprints'),
//         actions: [
//           IconButton(
//             icon: Icon(_isFlashOn ? Icons.flash_on : Icons.flash_off),
//             onPressed: () async {
//               if (_isFlashOn) {
//                 await _cameraController.setFlashMode(FlashMode.off);
//               } else {
//                 await _cameraController.setFlashMode(FlashMode.torch);
//               }
//               setState(() {
//                 _isFlashOn = !_isFlashOn;
//               });
//             },
//           ),
//         ],
//       ),
//       body: _isCameraInitialized
//           ? Stack(
//               children: [
//                 CameraPreview(_cameraController),
//                 _buildArcOverlay(), // Overlay to guide finger positioning
//                 Align(
//                   alignment: Alignment.bottomCenter,
//                   child: Padding(
//                     padding: const EdgeInsets.all(16.0),
//                     child: ElevatedButton(
//                       onPressed: _imageCount < _captureOrder.length
//                           ? () async {
//                               String currentPhase = _captureOrder[_imageCount];
//                               await _captureImage(currentPhase);
//                               setState(() {
//                                 _imageCount++;
//                               });

//                               if (_imageCount == _captureOrder.length) {
//                                 ScaffoldMessenger.of(context).showSnackBar(
//                                   const SnackBar(
//                                     content: Text(
//                                         'All images captured successfully!'),
//                                   ),
//                                 );
//                                 // Optionally perform an action after capturing all images
//                               }
//                             }
//                           : null, // Disable the button if all images are captured
//                       child: Text(_imageCount < _captureOrder.length
//                           ? 'Capture ${_captureOrder[_imageCount]}'
//                           : 'All Captured'),
//                     ),
//                   ),
//                 ),
//               ],
//             )
//           : const Center(child: CircularProgressIndicator()),
//     );
//   }
// }

// class ArcPainter extends CustomPainter {
//   @override
//   void paint(Canvas canvas, Size size) {
//     final Paint paint = Paint()
//       ..color = Colors.red.withOpacity(0.5) // Arc color and transparency
//       ..strokeWidth = 4.0
//       ..style = PaintingStyle.stroke;

//     final double arcHeight = size.height / 2;
//     final double arcWidth = size.width - 40;

//     // Draw an arc shape on the camera view for better alignment
//     final Rect arcRect = Rect.fromCenter(
//       center: Offset(size.width / 2, size.height / 2),
//       width: arcWidth,
//       height: arcHeight,
//     );
//     canvas.drawArc(arcRect, 3.14, 3.14, false, paint); // Draw a half-circle
//   }

//   @override
//   bool shouldRepaint(covariant CustomPainter oldDelegate) {
//     return false;
//   }
// }