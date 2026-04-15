# import cv2
# import mediapipe as mp
# import numpy as np
# import pygame
# from pygame.locals import *
# from OpenGL.GL import *
# from OpenGL.GLU import *
# from OpenGL.GLUT import *  # For glutInit, if available
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Initialize MediaPipe Hands
# mp_hands = mp.solutions.hands
# hands = mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=2,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )

# # Initialize Pygame and OpenGL
# pygame.init()
# display = (800, 600)
# try:
#     pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
# except pygame.error as e:
#     logger.error(f"Failed to initialize Pygame OpenGL display: {str(e)}")
#     raise

# # Try initializing GLUT (may help with GLU functions on some systems)
# try:
#     glutInit()
# except NameError as e:
#     logger.warning("GLUT not available, proceeding without it")

# # Set up perspective projection manually
# def setup_projection():
#     glMatrixMode(GL_PROJECTION)
#     glLoadIdentity()
#     # Manual perspective setup using glFrustum (replacing gluPerspective)
#     aspect = display[0] / display[1]
#     fov = 45.0
#     near = 0.1
#     far = 50.0
#     fovy = np.tan(np.radians(fov) / 2.0)
#     glFrustum(-fovy * aspect, fovy * aspect, -fovy, fovy, near, far)
#     glMatrixMode(GL_MODELVIEW)
#     glLoadIdentity()
#     glTranslatef(0.0, 0.0, -5.0)

# try:
#     setup_projection()
# except Exception as e:
#     logger.error(f"Failed to set up OpenGL projection: {str(e)}")
#     raise

# # Function to render hand landmarks using OpenGL
# def render_hands(hands_result):
#     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
#     glBegin(GL_POINTS)
#     glColor3f(1.0, 0.0, 0.0)  # Red points for landmarks
#     if hands_result.multi_hand_landmarks:
#         for hand_landmarks in hands_result.multi_hand_landmarks:
#             for landmark in hand_landmarks.landmark:
#                 # Map normalized [0,1] coordinates to OpenGL [-1,1]
#                 x = (landmark.x * 2 - 1) * (display[0] / display[1])
#                 y = -(landmark.y * 2 - 1)  # Invert y for OpenGL
#                 glVertex3f(x, y, 0.0)
#     glEnd()
#     pygame.display.flip()

# # Function to process webcam input
# def process_webcam():
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         logger.error("Cannot open webcam")
#         return

#     try:
#         while cap.isOpened():
#             success, frame = cap.read()
#             if not success:
#                 logger.error("Cannot read frame from webcam")
#                 break

#             # Convert BGR to RGB for MediaPipe
#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             # Process frame with MediaPipe Hands
#             results = hands.process(frame_rgb)

#             if results.multi_hand_landmarks:
#                 # Log wrist coordinates for first hand
#                 wrist = results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
#                 logger.info(f"Hand wrist normalized coordinates: x={wrist.x:.3f}, y={wrist.y:.3f}")

#                 # Render results
#                 render_hands(results)

#             # Display webcam feed with landmarks
#             frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
#             if results.multi_hand_landmarks:
#                 for hand_landmarks in results.multi_hand_landmarks:
#                     mp.solutions.drawing_utils.draw_landmarks(
#                         frame_bgr, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#             cv2.imshow('MediaPipe Hands', frame_bgr)
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break

#             # Handle Pygame events
#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     cap.release()
#                     cv2.destroyAllWindows()
#                     pygame.quit()
#                     return

#     except Exception as e:
#         logger.error(f"Error processing webcam: {str(e)}")
#     finally:
#         cap.release()
#         cv2.destroyAllWindows()
#         pygame.quit()

# # Main execution
# if __name__ == "__main__":
#     process_webcam()


import cv2
import mediapipe as mp
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Initialize Pygame and OpenGL
pygame.init()
display = (800, 600)
try:
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
except pygame.error as e:
    logger.error(f"Failed to initialize Pygame OpenGL display: {str(e)}")
    raise

# Set up perspective projection manually
def setup_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Manual perspective setup using glFrustum
    aspect = display[0] / display[1]
    fov = 45.0
    near = 0.1
    far = 50.0
    fovy = np.tan(np.radians(fov) / 2.0)
    glFrustum(-fovy * aspect, fovy * aspect, -fovy, fovy, near, far)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -5.0)

try:
    setup_projection()
except Exception as e:
    logger.error(f"Failed to set up OpenGL projection: {str(e)}")
    raise

# Function to render hand landmarks  using OpenGL
def render_hands(hands_result):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glBegin(GL_POINTS)
    glColor3f(1.0, 0.0, 0.0)  # Red points for landmarks
    if hands_result.multi_hand_landmarks:
        for hand_landmarks in hands_result.multi_hand_landmarks:
            for landmark in hand_landmarks.landmark:
                # Map normalized [0,1] coordinates to OpenGL [-1,1]
                x = (landmark.x * 2 - 1) * (display[0] / display[1])
                y = -(landmark.y * 2 - 1)  # Invert y for OpenGL
                glVertex3f(x, y, 0.0)
    glEnd()
    pygame.display.flip()

# Function to process webcam input
def process_webcam():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return

    # Define finger names and corresponding landmark indices
    finger_names = {
        mp_hands.HandLandmark.THUMB_TIP: "Thumb",
        mp_hands.HandLandmark.INDEX_FINGER_TIP: "Index",
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP: "Middle",
        mp_hands.HandLandmark.RING_FINGER_TIP: "Ring",
        mp_hands.HandLandmark.PINKY_TIP: "Pinky"
    }

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                logger.error("Cannot read frame from webcam")
                break

            # Get frame dimensions
            frame_height, frame_width = frame.shape[:2]

            # Convert BGR to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Process frame with MediaPipe Hands
            results = hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                # Log wrist coordinates for first hand
                wrist = results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
                logger.info(f"Hand wrist normalized coordinates: x={wrist.x:.3f}, y={wrist.y:.3f}")

                # Render results in OpenGL
                render_hands(results)

                # Draw landmarks and finger names on OpenCV frame
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                    # Get hand label (Left or Right)
                    hand_label = handedness.classification[0].label  # 'Left' or 'Right'
                    mp_drawing.draw_landmarks(
                        frame_bgr, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Annotate finger names at fingertip landmarks
                    for landmark_idx, finger_name in finger_names.items():
                        landmark = hand_landmarks.landmark[landmark_idx]
                        # Convert normalized coordinates to pixel coordinates
                        x = int(landmark.x * frame_width)
                        y = int(landmark.y * frame_height)
                        # Draw finger name with hand label (e.g., "Left Thumb")
                        cv2.putText(
                            frame_bgr,
                            f"{hand_label} {finger_name}",
                            (x, y - 10),  # Slightly above the landmark
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,  # Font scale
                            (0, 255, 0),  # Green text
                            1,  # Thickness
                            cv2.LINE_AA
                        )

            else:
                # No hands detected, use original frame
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            # Display webcam feed with landmarks and labels
            cv2.imshow('MediaPipe Hands', frame_bgr)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    cv2.destroyAllWindows()
                    pygame.quit()
                    return

    except Exception as e:
        logger.error(f"Error processing webcam: {str(e)}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pygame.quit()

# Main execution
if __name__ == "__main__":
    process_webcam()
