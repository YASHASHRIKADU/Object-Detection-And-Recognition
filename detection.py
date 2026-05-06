import cv2
import sqlite3
import datetime
import pyttsx3
from ultralytics import YOLO
import time
import threading

# Load YOLO model
model = YOLO("yolov8n.pt")

# Database setup
db = "database.db"
con = sqlite3.connect(db)
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS detections(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_name TEXT,
    confidence REAL,
    detected_time TEXT
)
""")

# Text to Speech function (create engine → speak → close)
def play_tts(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# Open camera
cap = cv2.VideoCapture(0)

last_spoken = ""
last_time = 0

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera not opened")
        break

    # Run YOLO detection
    results = model(frame)

    for r in results:
        for box in r.boxes:

            # Extract object data
            cls = int(box.cls[0])
            label = model.names[cls]
            conf = float(box.conf[0])

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

            text = f"{label} {conf:.2f}"

            cv2.putText(frame, text, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0,255,0),
                        2)

            # Speak only when new object appears or after delay
            if label != last_spoken or time.time() - last_time > 3:

                # Run speech in separate thread (prevents camera freeze)
                threading.Thread(target=play_tts, args=(label + " detected",), daemon=True).start()

                last_spoken = label
                last_time = time.time()

                # Save detection to database
                now = str(datetime.datetime.now())
                cur.execute(
                    "INSERT INTO detections(object_name,confidence,detected_time) VALUES(?,?,?)",
                    (label, conf, now)
                )
                con.commit()

    # Show video
    cv2.imshow("Object Detection", frame)

    # Press ESC to exit
    if cv2.waitKey(1) == 27:
        break


# Cleanup
cap.release()
cv2.destroyAllWindows()
con.close()
