import cv2
import mediapipe as mp


def count_fingers(hand_landmarks, hand_label):
    """
    Count how many fingers are up.
    This is a simple rule-based finger counter.
    """

    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]

    fingers_up = 0

    # Thumb
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]

    if hand_label == "Right":
        if thumb_tip.x < thumb_ip.x:
            fingers_up += 1
    else:
        if thumb_tip.x > thumb_ip.x:
            fingers_up += 1

    # Other four fingers
    for tip_id, pip_id in zip(finger_tips, finger_pips):
        tip = hand_landmarks.landmark[tip_id]
        pip = hand_landmarks.landmark[pip_id]

        if tip.y < pip.y:
            fingers_up += 1

    return fingers_up


def start_hand_tracking():
    """
    Start webcam and track hands using MediaPipe.
    Press 'q' to close the camera window.
    """

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return "Camera could not be opened."

    print("Hand tracking started. Press 'q' to stop.")

    while True:
        success, frame = camera.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)

        total_hands = 0
        total_fingers = 0

        if results.multi_hand_landmarks and results.multi_handedness:
            total_hands = len(results.multi_hand_landmarks)

            for index, (hand_landmarks, handedness) in enumerate(
                zip(results.multi_hand_landmarks, results.multi_handedness),
                start=1,
            ):
                hand_label = handedness.classification[0].label

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                )

                fingers = count_fingers(hand_landmarks, hand_label)
                total_fingers += fingers

                cv2.putText(
                    frame,
                    f"{hand_label} Hand: {fingers} fingers",
                    (10, 70 + index * 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

        cv2.putText(
            frame,
            f"Hands detected: {total_hands}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            f"Total fingers: {total_fingers}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Hand Tracking", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    hands.close()
    camera.release()
    cv2.destroyAllWindows()

    return "Hand tracking stopped."


if __name__ == "__main__":
    print(start_hand_tracking())