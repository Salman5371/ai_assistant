import cv2


def start_face_detection():
    """
    Start webcam and detect faces using OpenCV Haar Cascade.
    Press 'q' to close the camera window.
    """

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    if face_cascade.empty():
        return "Face detection model could not be loaded."

    camera = cv2.VideoCapture(0)

    try:
        if not camera.isOpened():
            return "Camera could not be opened."

        print("Face detection started. Press 'q' to stop.")

        while True:
            success, frame = camera.read()

            if not success:
                break

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            for (x, y, width, height) in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2
                )

            cv2.putText(
                frame,
                f"Faces detected: {len(faces)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow("Face Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return "Face detection stopped."

if __name__ == "__main__":
    print(start_face_detection())
