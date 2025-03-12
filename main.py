import cv2
import mediapipe as mp
import pyautogui

# Initialize webcam & hand tracking
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Get screen size for cursor scaling
screen_w, screen_h = pyautogui.size()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip frame horizontally for natural control
    frame = cv2.flip(frame, 1)
    frame_h, frame_w, _ = frame.shape

    # Convert to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Define image dimensions explicitly (Fixes the warning)
    image_rows, image_cols, _ = frame.shape
    image_size = (image_cols, image_rows)

    # Process hand tracking
    results = hands.process(frame_rgb)


    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get index finger tip coordinates (Landmark 8)
            index_finger = hand_landmarks.landmark[8]
            x, y = int(index_finger.x * frame_w), int(index_finger.y * frame_h)

            # Convert to screen coordinates
            cursor_x = int(index_finger.x * screen_w)
            cursor_y = int(index_finger.y * screen_h)

            # Move the mouse
            pyautogui.moveTo(cursor_x, cursor_y, duration=0.1)

            # Show cursor tracking
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)

    # Show webcam feed
    cv2.imshow("Virtual Mouse", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
