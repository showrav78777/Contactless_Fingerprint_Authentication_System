// import Flutter
// import UIKit

// @main
// @objc class AppDelegate: FlutterAppDelegate {
//   override func application(
//     _ application: UIApplication,
//     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
//   ) -> Bool {
//     GeneratedPluginRegistrant.register(with: self)
//     return super.application(application, didFinishLaunchingWithOptions: launchOptions)
//   }
// }




import Flutter
import UIKit
import MediaPipeTasksVision

@main
@objc class AppDelegate: FlutterAppDelegate {
  private var handLandmarker: HandLandmarker?
  private var resultProcessor: HandLandmarkerResultProcessor?
  private var methodChannel: FlutterMethodChannel?
  
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    print("=== iOS AppDelegate: Application starting ===")
    
    let controller = window?.rootViewController as! FlutterViewController
    let channel = FlutterMethodChannel(name: "com.example/mediapipe", binaryMessenger: controller.binaryMessenger)
    self.methodChannel = channel

    channel.setMethodCallHandler { (call: FlutterMethodCall, result: @escaping FlutterResult) in
      if call.method == "testConnection" {
        print("=== iOS: Testing MediaPipe connection ===")
        result(["success": true, "message": "MediaPipe connection test successful"])
        return
      }
      
      if call.method == "processFrame" {
        print("=== iOS: Received processFrame call ===")
        guard let args = call.arguments as? [String: Any],
              let data = args["data"] as? FlutterStandardTypedData,
              let width = args["width"] as? Int,
              let height = args["height"] as? Int else {
          print("iOS: Invalid arguments received")
          result(FlutterError(code: "INVALID_ARGUMENT", message: "Invalid arguments", details: nil))
          return
        }

        print("iOS: Processing frame with dimensions: \(width)x\(height)")
        let bytes = data.data
        print("iOS: Received \(bytes.count) bytes")
        
        var pixelBuffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(
          kCFAllocatorDefault,
          width,
          height,
          kCVPixelFormatType_32BGRA,
          [kCVPixelBufferCGImageCompatibilityKey: kCFBooleanTrue,
           kCVPixelBufferCGBitmapContextCompatibilityKey: kCFBooleanTrue] as CFDictionary,
          &pixelBuffer
        )

        guard status == kCVReturnSuccess, let buffer = pixelBuffer else {
          print("iOS: Failed to create CVPixelBuffer")
          result(FlutterError(code: "CONVERSION_ERROR", message: "Failed to create CVPixelBuffer", details: nil))
          return
        }

        print("iOS: Created CVPixelBuffer successfully")
        CVPixelBufferLockBaseAddress(buffer, [])
        let baseAddress = CVPixelBufferGetBaseAddress(buffer)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)
        let bufferSize = bytesPerRow * height

        // Ensure the input data size matches expected buffer size
        if bytes.count < width * height * 4 {
          CVPixelBufferUnlockBaseAddress(buffer, [])
          print("iOS: Data size mismatch - expected \(width * height * 4), got \(bytes.count)")
          result(FlutterError(code: "CONVERSION_ERROR", message: "Input data size (\(bytes.count)) is less than required (\(width * height * 4))", details: nil))
            return
          }

        print("iOS: Copying data to pixel buffer...")
        // Copy the BGRA data to the pixel buffer row by row
        if let baseAddress = baseAddress {
          let srcBytes = [UInt8](bytes)
          srcBytes.withUnsafeBytes { srcRawBuffer in
            let srcBase = srcRawBuffer.baseAddress!
            for row in 0..<height {
              let srcRowPtr = srcBase.advanced(by: row * width * 4)
              let dstRowPtr = baseAddress.advanced(by: row * bytesPerRow)
              memcpy(dstRowPtr, srcRowPtr, width * 4)
            }
          }
        }
        CVPixelBufferUnlockBaseAddress(buffer, [])
        print("iOS: Data copied to pixel buffer successfully")

        // Initialize MediaPipe HandLandmarker with live stream mode
        self.initializeHandLandmarkerIfNeeded()
        
        do {
          let image = try MPImage(pixelBuffer: buffer)
          print("iOS: Created MPImage successfully")
          
          // Use live stream mode for better performance
          let timestamp = Int(Date().timeIntervalSince1970 * 1000)
          try self.handLandmarker?.detectAsync(image: image, timestampInMilliseconds: timestamp)
          
          // The result will be processed asynchronously by the delegate
          result(["success": true, "message": "Frame sent for processing"])
          
        } catch {
          print("iOS: MediaPipe error: \(error)")
          result(FlutterError(code: "MEDIAPIPE_ERROR", message: "MediaPipe processing failed: \(error)", details: nil))
        }
      } else {
        print("iOS: Unknown method called: \(call.method)")
        result(FlutterMethodNotImplemented)
      }
    }

    GeneratedPluginRegistrant.register(with: self)
    print("=== iOS AppDelegate: Application setup complete ===")
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
  
  private func initializeHandLandmarkerIfNeeded() {
    guard handLandmarker == nil else { return }
    
    print("iOS: Initializing HandLandmarker with live stream mode...")
    
    // Look for the model file
    var modelPath: String?
    if let path = Bundle.main.path(forResource: "hand_landmarker", ofType: "task") {
      modelPath = path
    } else {
      print("iOS: Model file not found in bundle")
      if let altPath = Bundle.main.path(forResource: "hand_landmarker", ofType: "task", inDirectory: nil) {
        print("iOS: Found model at alternative path: \(altPath)")
        modelPath = altPath
      } else {
        print("iOS: Model file not found")
        return
      }
    }

    guard let finalModelPath = modelPath else {
      print("iOS: Model file not found")
      return
    }

    print("iOS: Found model at path: \(finalModelPath)")
    
    // Check if file exists and is readable
    let fileManager = FileManager.default
    if !fileManager.fileExists(atPath: finalModelPath) {
      print("iOS: Model file does not exist at path: \(finalModelPath)")
      return
    }
    
    do {
      let attributes = try fileManager.attributesOfItem(atPath: finalModelPath)
      if let fileSize = attributes[.size] as? NSNumber {
        print("iOS: Model file size: \(fileSize.intValue) bytes")
        if fileSize.intValue < 1000000 {
          print("iOS: WARNING - Model file seems too small!")
        }
      }
    } catch {
      print("iOS: Error getting file attributes: \(error)")
    }
    
    let options = HandLandmarkerOptions()
    options.runningMode = .liveStream
    // Lower thresholds for better detection
    options.minHandDetectionConfidence = 0.3
    options.minHandPresenceConfidence = 0.3
    options.minTrackingConfidence = 0.3
    options.numHands = 2
    options.baseOptions.modelAssetPath = finalModelPath
    
    // Create result processor with method channel reference
    self.resultProcessor = HandLandmarkerResultProcessor(methodChannel: self.methodChannel)
    options.handLandmarkerLiveStreamDelegate = self.resultProcessor
    
    print("iOS: Initializing HandLandmarker with live stream mode...")
    do {
      self.handLandmarker = try HandLandmarker(options: options)
      print("iOS: HandLandmarker initialized successfully with live stream mode")
    } catch {
      print("iOS: Error initializing HandLandmarker: \(error)")
    }
  }
}

// Class that conforms to the `HandLandmarkerLiveStreamDelegate` protocol
class HandLandmarkerResultProcessor: NSObject, HandLandmarkerLiveStreamDelegate {
  private weak var methodChannel: FlutterMethodChannel?
  
  init(methodChannel: FlutterMethodChannel?) {
    self.methodChannel = methodChannel
    super.init()
  }
  
  func handLandmarker(
    _ handLandmarker: HandLandmarker,
    didFinishDetection result: HandLandmarkerResult?,
    timestampInMilliseconds: Int,
    error: Error?) {
    
    if let error = error {
      print("iOS: HandLandmarker error: \(error)")
      return
    }
    
    guard let result = result else {
      print("iOS: No hand landmarker result")
      return
    }
    
    print("iOS: Processing live stream result...")
    
    var landmarks: [[String: Any]] = []
    var handedness: [String] = []
    var confidences: [Float] = []
    
    let results = result.landmarks
    print("iOS: Found \(results.count) hands")
    
    for (handIndex, handLandmarks) in results.enumerated() {
      print("iOS: Processing hand \(handIndex) with \(handLandmarks.count) landmarks")
      for landmark in handLandmarks {
        landmarks.append([
          "x": Float(landmark.x),
          "y": Float(landmark.y),
          "z": Float(landmark.z)
        ])
      }
    }
    
    let classifications = result.handedness
    print("iOS: Processing handedness classifications...")
    for (index, classification) in classifications.enumerated() {
      if let category = classification.first {
        let handednessName = category.categoryName ?? "Unknown"
        let confidence = category.score
        print("iOS: Hand \(index) - \(handednessName) with confidence \(confidence)")
        handedness.append(handednessName)
        confidences.append(confidence)
      }
    }
    
    print("iOS: Live stream result - \(landmarks.count) landmarks, \(handedness.count) handedness, \(confidences.count) confidences")
    
    // Send result back to Flutter via method channel
    let resultData: [String: Any] = [
      "landmarks": landmarks,
      "handedness": handedness,
      "confidences": confidences,
      "success": true
    ]
    
    DispatchQueue.main.async {
      self.methodChannel?.invokeMethod("handResult", arguments: resultData)
    }
  }
}