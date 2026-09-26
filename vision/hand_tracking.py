from pathlib import Path
import time
import math

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from automation.app_control import open_website


# Optional vision logger support
try:
    from vision.vision_logger import log_vision_event
except Exception:
    def log_vision_event(event_text):
        pass


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
HAND_MODEL = MODELS_DIR / "hand_landmarker.task"

MIRROR_VIEW = True
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

GOOGLE_URL = "https://www.google.com"
YOUTUBE_URL = "https://www.youtube.com"


def swap_hand_label(label):
    """
    Camera view is mirrored, so swap Left/Right for display.
    """
    if label == "Left":
        return "Right"
    if label == "Right":
        return "Left"
    return label


def get_distance(point1, point2):
    """
    Calculate distance between two landmarks.
    """
    x_distance = point1.x - point2.x
    y_distance = point1.y - point2.y
    z_distance = point1.z - point2.z

    return math.sqrt(
        x_distance ** 2
        + y_distance ** 2
        + z_distance ** 2
    )


def get_finger_states(hand_landmarks):
    """
    Return which fingers are up.
    """

    wrist = hand_landmarks[0]

    thumb_tip = hand_landmarks[4]
    thumb_ip = hand_landmarks[3]
    thumb_mcp = hand_landmarks[2]

    index_mcp = hand_landmarks[5]
    middle_mcp = hand_landmarks[9]

    palm_size = get_distance(wrist, middle_mcp)

    if palm_size == 0:
        return {
            "thumb": False,
            "index": False,
            "middle": False,
            "ring": False,
            "pinky": False,
        }

    # Thumb detection
    thumb_to_index = get_distance(thumb_tip, index_mcp)
    thumb_ip_to_index = get_distance(thumb_ip, index_mcp)
    thumb_tip_to_mcp = get_distance(thumb_tip, thumb_mcp)
    thumb_ip_to_mcp = get_distance(thumb_ip, thumb_mcp)

    thumb_up = (
        thumb_to_index > palm_size * 0.45
        and thumb_tip_to_mcp > thumb_ip_to_mcp * 1.10
        and thumb_to_index > thumb_ip_to_index * 1.05
    )

    finger_data = {
        "index": (8, 6),
        "middle": (12, 10),
        "ring": (16, 14),
        "pinky": (20, 18),
    }

    states = {
        "thumb": thumb_up,
        "index": False,
        "middle": False,
        "ring": False,
        "pinky": False,
    }

    for finger_name, (tip_id, pip_id) in finger_data.items():
        tip = hand_landmarks[tip_id]
        pip = hand_landmarks[pip_id]

        tip_distance = get_distance(wrist, tip)
        pip_distance = get_distance(wrist, pip)

        is_extended_by_distance = tip_distance > pip_distance * 1.08
        is_extended_by_position = tip.y < pip.y

        states[finger_name] = is_extended_by_distance or is_extended_by_position

    return states


def detect_gesture(hand_landmarks):
    """
    Detect gesture from finger states.

    Gestures:
    - Open Palm
    - Fist
    - One Finger
    - Two Fingers
    - Thumbs Up
    """

    states = get_finger_states(hand_landmarks)

    thumb = states["thumb"]
    index = states["index"]
    middle = states["middle"]
    ring = states["ring"]
    pinky = states["pinky"]

    finger_count = sum(1 for is_up in states.values() if is_up)

    thumb_tip = hand_landmarks[4]
    thumb_mcp = hand_landmarks[2]

    # Thumbs Up: thumb open and other fingers closed
    if thumb and not index and not middle and not ring and not pinky and thumb_tip.y < thumb_mcp.y:
        return "Thumbs Up", finger_count

    # Fist
    if finger_count == 0:
        return "Fist", finger_count

    # One Finger: only index finger
    if index and not thumb and not middle and not ring and not pinky:
        return "One Finger", finger_count

    # Two Fingers: index + middle
    if index and middle and not thumb and not ring and not pinky:
        return "Two Fingers", finger_count

    # Open Palm
    if finger_count >= 4:
        return "Open Palm", finger_count

    return "Unknown Gesture", finger_count


def get_hand_box(hand_landmarks, frame_width, frame_height):
    """
    Get bounding box around hand landmarks.
    """
    x_points = [int(landmark.x * frame_width) for landmark in hand_landmarks]
    y_points = [int(landmark.y * frame_height) for landmark in hand_landmarks]

    x1 = max(0, min(x_points) - 20)
    y1 = max(0, min(y_points) - 20)
    x2 = min(frame_width, max(x_points) + 20)
    y2 = min(frame_height, max(y_points) + 20)

    return x1, y1, x2, y2


def draw_text_with_background(
    frame,
    text,
    position,
    font_scale=0.65,
    text_color=(0, 255, 0),
    background_color=(0, 0, 0),
    thickness=2,
    padding=6,
):
    """
    Draw readable text with small background.
    """
    x, y = position
    font = cv2.FONT_HERSHEY_SIMPLEX

    text_size, baseline = cv2.getTextSize(text, font, font_scale, thickness)
    text_width, text_height = text_size

    cv2.rectangle(
        frame,
        (x - padding, y - text_height - padding),
        (x + text_width + padding, y + baseline + padding),
        background_color,
        -1,
    )

    cv2.putText(
        frame,
        text,
        (x, y),
        font,
        font_scale,
        text_color,
        thickness,
        cv2.LINE_AA,
    )


def draw_hand_landmarks(frame, hand_landmarks):
    """
    Draw hand landmark points and connections manually.
    """
    frame_height, frame_width, _ = frame.shape

    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (17, 18), (18, 19), (19, 20),
        (0, 17),
    ]

    points = []

    for landmark in hand_landmarks:
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        points.append((x, y))

    for start, end in connections:
        cv2.line(frame, points[start], points[end], (0, 255, 0), 2)

    for point in points:
        cv2.circle(frame, point, 5, (0, 0, 255), -1)


def draw_transparent_panel(frame, x1, y1, x2, y2, alpha=0.45):
    """
    Draw semi-transparent panel.
    """
    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (x1, y1),
        (x2, y2),
        (0, 0, 0),
        -1,
    )

    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def draw_info_panel(frame, total_hands, total_fingers, fps, assistant_active, last_action):
    """
    Draw information panel on top-right.
    """
    frame_height, frame_width, _ = frame.shape

    panel_width = 500
    panel_height = 185

    x1 = frame_width - panel_width - 10
    y1 = 10
    x2 = frame_width - 10
    y2 = y1 + panel_height

    draw_transparent_panel(frame, x1, y1, x2, y2, alpha=0.45)

    text_x = x1 + 15

    status = "ACTIVE" if assistant_active else "LOCKED"
    status_color = (0, 255, 0) if assistant_active else (0, 165, 255)

    cv2.putText(
        frame,
        f"Gesture Assistant: {status}",
        (text_x, y1 + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        status_color,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"Hands: {total_hands} | Fingers: {total_fingers}",
        (text_x, y1 + 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "Right: Palm=Active, 1=Google, 2=YouTube, Thumb=Confirm",
        (text_x, y1 + 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.47,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "Left: Fist=Stop camera",
        (text_x, y1 + 132),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"FPS: {fps:.1f} | Last: {last_action}",
        (text_x, y1 + 165),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def handle_gesture_action(gesture_name, hand_label, assistant_active):
    """
    Run action based on gesture and hand side.

    Right hand:
    - Open Palm = activate assistant
    - One Finger = open Google
    - Two Fingers = open YouTube
    - Thumbs Up = confirm

    Left hand:
    - Fist = stop camera
    """

    # Left hand fist = stop camera
    if hand_label == "Left" and gesture_name == "Fist":
        log_vision_event("Left hand fist detected. Camera stopped.")
        return assistant_active, "Left fist: Stopping camera", True

    # Left hand other gestures = no action
    if hand_label == "Left":
        return assistant_active, "Left hand ignored", False

    # Right hand open palm = activate
    if hand_label == "Right" and gesture_name == "Open Palm":
        log_vision_event("Right hand open palm detected. Assistant activated.")
        return True, "Right palm: Activated", False

    # If locked, ignore right hand commands except open palm
    if not assistant_active:
        log_vision_event(f"Right hand gesture while locked: {gesture_name}")
        return assistant_active, "Show right palm to activate", False

    # Right hand one finger = Google
    if hand_label == "Right" and gesture_name == "One Finger":
        open_website(GOOGLE_URL)
        log_vision_event("Right hand one finger: Opened Google.")
        return assistant_active, "Right 1: Google", False

    # Right hand two fingers = YouTube
    if hand_label == "Right" and gesture_name == "Two Fingers":
        open_website(YOUTUBE_URL)
        log_vision_event("Right hand two fingers: Opened YouTube.")
        return assistant_active, "Right 2: YouTube", False

    # Right hand thumbs up = confirm
    if hand_label == "Right" and gesture_name == "Thumbs Up":
        log_vision_event("Right hand thumbs up: Confirmed.")
        return assistant_active, "Right thumbs up: Confirmed", False

    # Right hand fist = ignore
    if hand_label == "Right" and gesture_name == "Fist":
        return assistant_active, "Right fist ignored", False

    return assistant_active, "No action", False


def start_hand_tracking():
    """
    Start webcam and track hands using MediaPipe Tasks API.

    Rules:
    Right Open Palm = activate assistant
    Right One Finger = open Google
    Right Two Fingers = open YouTube
    Right Thumbs Up = confirm
    Left Fist = stop camera

    Press 'q' to close the camera window.
    """

    if not HAND_MODEL.exists():
        return "Hand landmarker model is missing. Please add hand_landmarker.task inside the models folder."

    if HAND_MODEL.stat().st_size < 1000000:
        return "Hand landmarker model seems corrupted or incomplete. Please download hand_landmarker.task again."

    base_options = python.BaseOptions(model_asset_path=str(HAND_MODEL))

    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    camera = cv2.VideoCapture(0)

    try:
        if not camera.isOpened():
            return "Camera could not be opened."

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)

        cv2.namedWindow("Gesture Controlled Assistant", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Gesture Controlled Assistant", WINDOW_WIDTH, WINDOW_HEIGHT)

        log_vision_event("Hand-specific gesture control started.")
        print("Hand-specific gesture control started. Press 'q' to stop.")

        start_time = time.time()
        previous_time = time.time()

        assistant_active = False
        last_action = "Waiting"
        last_gesture = None
        last_action_time = 0

        action_cooldown = 3
        should_stop_camera = False

        with vision.HandLandmarker.create_from_options(options) as landmarker:
            while True:
                success, frame = camera.read()

                if not success:
                    break

                if MIRROR_VIEW:
                    frame = cv2.flip(frame, 1)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame,
                )

                timestamp_ms = int((time.time() - start_time) * 1000)
                result = landmarker.detect_for_video(mp_image, timestamp_ms)

                total_hands = 0
                total_fingers = 0

                current_time = time.time()
                fps = 1 / (current_time - previous_time) if current_time != previous_time else 0
                previous_time = current_time

                frame_height, frame_width, _ = frame.shape

                if result.hand_landmarks:
                    total_hands = len(result.hand_landmarks)

                    for index, hand_landmarks in enumerate(result.hand_landmarks):
                        detected_label = "Unknown"

                        if result.handedness and len(result.handedness) > index:
                            detected_label = result.handedness[index][0].category_name

                        display_label = swap_hand_label(detected_label) if MIRROR_VIEW else detected_label

                        gesture_name, fingers = detect_gesture(hand_landmarks)
                        total_fingers += fingers

                        x1, y1, x2, y2 = get_hand_box(
                            hand_landmarks,
                            frame_width,
                            frame_height,
                        )

                        cv2.rectangle(
                            frame,
                            (x1, y1),
                            (x2, y2),
                            (0, 255, 0),
                            2,
                        )

                        draw_hand_landmarks(frame, hand_landmarks)

                        label_text = f"{display_label}: {gesture_name} ({fingers})"

                        label_y = y2 + 30

                        if label_y > frame_height - 20:
                            label_y = y1 - 15

                        if label_y < 30:
                            label_y = 30

                        draw_text_with_background(
                            frame,
                            label_text,
                            (x1, label_y),
                            font_scale=0.65,
                            text_color=(0, 255, 0),
                        )

                        gesture_key = f"{display_label}:{gesture_name}"

                        can_run_action = (
                            gesture_name != "Unknown Gesture"
                            and (
                                gesture_key != last_gesture
                                or current_time - last_action_time > action_cooldown
                            )
                        )

                        if can_run_action:
                            assistant_active, last_action, should_stop_camera = handle_gesture_action(
                                gesture_name,
                                display_label,
                                assistant_active,
                            )

                            if should_stop_camera:
                                break

                            last_gesture = gesture_key
                            last_action_time = current_time

                else:
                    last_gesture = None

                draw_info_panel(
                    frame,
                    total_hands,
                    total_fingers,
                    fps,
                    assistant_active,
                    last_action,
                )

                cv2.imshow("Gesture Controlled Assistant", frame)

                if should_stop_camera:
                    time.sleep(1)
                    break

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    log_vision_event("Hand-specific gesture control stopped.")
    return "Hand-specific gesture control stopped."


if __name__ == "__main__":
    print(start_hand_tracking())
