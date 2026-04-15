import Foundation
import MediaPipeTasksVision
import AVFoundation

@objc class MediaPipeHandler: NSObject {
    @objc static func processFrame(_ pixelBuffer: CVPixelBuffer, completion: @escaping ([String: Any]) -> Void) {
        // Load the hand landmarker model (make sure hand_landmarker.task is in your app bundle)
        guard let modelPath = Bundle.main.path(forResource: "hand_landmarker", ofType: "task") else {
            completion(["error": "Model not found", "success": false])
            return
        }
        let options = HandLandmarkerOptions()
        options.baseOptions.modelAssetPath = modelPath
        options.runningMode = .image
        options.numHands = 2
        options.minHandDetectionConfidence = 0.3
        options.minHandPresenceConfidence = 0.5
        options.minTrackingConfidence = 0.5

        do {
            let landmarker = try HandLandmarker(options: options)
            let mpImage = try MPImage(pixelBuffer: pixelBuffer)
            let result = try landmarker.detect(image: mpImage)
        var landmarksData: [[String: Double]] = []
            var handednessData: [String] = []
            var confidences: [Double] = []
            let multiHandLandmarks = result.landmarks
            let multiHandedness = result.handedness
            for (i, landmarks) in multiHandLandmarks.enumerated() {
                let handLabel = multiHandedness[i].first?.displayName ?? multiHandedness[i].first?.categoryName ?? "Unknown"
                handednessData.append(handLabel)
                confidences.append(Double(multiHandedness[i].first?.score ?? 0.0))
                    let landmarkPoints = landmarks.map { landmark in
                        ["x": Double(landmark.x), "y": Double(landmark.y), "z": Double(landmark.z)]
                    }
                    landmarksData.append(contentsOf: landmarkPoints)
                }
            completion([
                "landmarks": landmarksData,
                "handedness": handednessData,
                "confidences": confidences,
                "success": true
            ])
        } catch {
            completion(["error": error.localizedDescription, "success": false])
        }
    }
}