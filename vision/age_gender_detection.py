from pathlib import Path
from vision.vision_logger import log_vision_event
import cv2


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

FACE_PROTO = MODELS_DIR / "opencv_face_detector.pbtxt"
FACE_MODEL = MODELS_DIR / "opencv_face_detector_uint8.pb"

AGE_PROTO = MODELS_DIR / "age_deploy.prototxt"
AGE_MODEL = MODELS_DIR / "age_net.caffemodel"

GENDER_PROTO = MODELS_DIR / "gender_deploy.prototxt"
GENDER_MODEL = MODELS_DIR / "gender_net.caffemodel"


AGE_LIST = [
    "(0-2)",
    "(4-6)",
    "(8-12)",
    "(15-20)",
    "(25-32)",
    "(38-43)",
    "(48-53)",
    "(60-100)",
]

GENDER_LIST = ["Male", "Female"]

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)


def check_model_files():
    required_files = [
        FACE_PROTO,
        FACE_MODEL,
        AGE_PROTO,
        AGE_MODEL,
        GENDER_PROTO,
        GENDER_MODEL,
    ]

    missing_files = []

    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(file_path.name)

    if missing_files:
        return False, missing_files

    return True, []


def get_face_boxes(face_net, frame, confidence_threshold=0.7):
    frame_copy = frame.copy()
    frame_height = frame_copy.shape[0]
    frame_width = frame_copy.shape[1]

    blob = cv2.dnn.blobFromImage(
        frame_copy,
        1.0,
        (300, 300),
        [104, 117, 123],
        True,
        False,
    )

    face_net.setInput(blob)
    detections = face_net.forward()

    face_boxes = []

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > confidence_threshold:
            x1 = int(detections[0, 0, i, 3] * frame_width)
            y1 = int(detections[0, 0, i, 4] * frame_height)
            x2 = int(detections[0, 0, i, 5] * frame_width)
            y2 = int(detections[0, 0, i, 6] * frame_height)

            face_boxes.append([x1, y1, x2, y2])

    return face_boxes


def start_age_gender_detection():
    """
    Start webcam and detect face, gender label, and age range.
    Press 'q' to close the camera window.
    """

    models_ok, missing_files = check_model_files()

    if not models_ok:
        return (
            "Model files are missing: "
            + ", ".join(missing_files)
            + ". Please add them inside the models folder."
        )

    face_net = cv2.dnn.readNet(str(FACE_MODEL), str(FACE_PROTO))
    age_net = cv2.dnn.readNet(str(AGE_MODEL), str(AGE_PROTO))
    gender_net = cv2.dnn.readNet(str(GENDER_MODEL), str(GENDER_PROTO))

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return "Camera could not be opened."
    
    log_vision_event("Age and gender detection started.")

    print("Age and gender detection started. Press 'q' to stop.")

    padding = 20

    while True:
        success, frame = camera.read()

        if not success:
            break

        face_boxes = get_face_boxes(face_net, frame)

        for face_box in face_boxes:
            x1, y1, x2, y2 = face_box

            face = frame[
                max(0, y1 - padding): min(y2 + padding, frame.shape[0] - 1),
                max(0, x1 - padding): min(x2 + padding, frame.shape[1] - 1),
            ]

            if face.size == 0:
                continue

            blob = cv2.dnn.blobFromImage(
                face,
                1.0,
                (227, 227),
                MODEL_MEAN_VALUES,
                swapRB=False,
            )

            gender_net.setInput(blob)
            gender_predictions = gender_net.forward()
            gender = GENDER_LIST[gender_predictions[0].argmax()]
            gender_confidence = gender_predictions[0].max() * 100

            age_net.setInput(blob)
            age_predictions = age_net.forward()
            age = AGE_LIST[age_predictions[0].argmax()]
            age_confidence = age_predictions[0].max() * 100

            label = f"{gender} {gender_confidence:.1f}% | Age {age} {age_confidence:.1f}%"

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        cv2.putText(
            frame,
            f"Faces detected: {len(face_boxes)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Age and Gender Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    log_vision_event("Age and gender detection stopped.")

    return "Age and gender detection stopped."


if __name__ == "__main__":
    print(start_age_gender_detection())