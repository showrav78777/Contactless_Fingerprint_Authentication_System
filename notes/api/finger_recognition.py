import cv2
import mediapipe as mp
import numpy as np
import logging
import os
import glob
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.5
)

# Define finger names and corresponding landmark indices
finger_names = {
    mp_hands.HandLandmark.THUMB_TIP: "Thumb",
    mp_hands.HandLandmark.INDEX_FINGER_TIP: "Index",
    mp_hands.HandLandmark.MIDDLE_FINGER_TIP: "Middle",
    mp_hands.HandLandmark.RING_FINGER_TIP: "Ring",
    mp_hands.HandLandmark.PINKY_TIP: "Pinky"
}

def recognize_hand(image_bytes):
    """
    Process an image, draw landmarks and finger names, and return annotated image URL.
    """
    try:
        # Decode image from bytes
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            logger.error("Failed to decode image")
            return {'error': 'Invalid image format'}

        # Preprocess image: resize and adjust brightness/contrast
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)
        frame_height, frame_width = frame.shape[:2]
        logger.info(f"Image dimensions: width={frame_width}, height={frame_height}")

        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        # Process image with MediaPipe Hands
        results = hands.process(frame_rgb)

        # Prepare response data
        response_data = {
            'hands_detected': False,
            'processed_image_url': None
        }

        if results.multi_hand_landmarks:
            response_data['hands_detected'] = True
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                hand_label = handedness.classification[0].label
                logger.info(f"Hand {idx + 1} - Label: {hand_label}")
                
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                logger.info(f"  Wrist normalized coordinates: x={wrist.x:.3f}, y={wrist.y:.3f}")

                # Draw landmarks and annotate finger names
                mp_drawing.draw_landmarks(frame_bgr, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                for landmark_idx, finger_name in finger_names.items():
                    landmark = hand_landmarks.landmark[landmark_idx]
                    x = int(landmark.x * frame_width)
                    y = int(landmark.y * frame_height)
                    cv2.putText(
                        frame_bgr,
                        f"{hand_label} {finger_name}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                        cv2.LINE_AA
                    )
                    logger.info(f"  {hand_label} {finger_name}: x={x:.1f}, y={y:.1f}, z={landmark.z:.3f}")

            # Save annotated image
            debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            debug_files = glob.glob(os.path.join(debug_dir, 'hand_debug_*.jpg'))
            if len(debug_files) > 10:
                for old_file in debug_files[:-10]:
                    os.remove(old_file)
            debug_path = os.path.join(debug_dir, f"hand_debug_{int(np.random.rand() * 1000000)}.jpg")
            cv2.imwrite(debug_path, frame_bgr)
            response_data['processed_image_url'] = os.path.relpath(debug_path, settings.MEDIA_ROOT).replace(os.sep, '/')

        return response_data

    except Exception as e:
        logger.error(f"Error in recognize_hand: {str(e)}")
        return {'error': str(e)}