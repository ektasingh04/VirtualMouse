import cv2
import mediapipe as mp
import pyautogui
import util
from pynput.mouse import Button, Controller
import random

screen_width, screen_height = pyautogui.size()
mouse = Controller()
mpHands = mp.solutions.hands
hands = mpHands.Hands(
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1,
)


# Frame counters for gesture stability
gesture_frames = {
    "left_click": 0,
    "right_click": 0,
    "double_click": 0,
    "scroll": 0,
    "zoom_in": 0,
    "zoom_out": 0,
    "screenshot": 0
}
FRAME_THRESHOLD = 7  # Adjust for sensitivity
def fingers_up(landmarks):
    fingers = []
    tip_ids = [4, 8, 12, 16, 20]

    # Thumb
    if landmarks[tip_ids[0]][0] > landmarks[tip_ids[0]-1][0]:
        fingers.append(1)
    else:
        fingers.append(0)

    # Fingers
    for id in range(1,5):
        if landmarks[tip_ids[id]][1] < landmarks[tip_ids[id]-2][1]:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

def find_finger_tip(processed):
    if processed.multi_hand_landmarks:
        hand_landmarks = processed.multi_hand_landmarks[0]
        return hand_landmarks.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP]
    return None

def move_mouse(index_tip):
    if index_tip is not None:
        x = int(index_tip.x * screen_width)
        y = int(index_tip.y * screen_height)
        pyautogui.moveTo(x, y, duration=0.1)

def is_left_click(landmarks_list, thumb_index_dist):
    return (util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) < 50 and 
            util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) > 90 and
            thumb_index_dist > 50)

def is_right_click(landmarks_list, thumb_index_dist):
    return (util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) > 90 and 
            util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) < 50 and
            thumb_index_dist > 50)

def is_double_click(landmarks_list, thumb_index_dist):
    return (util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) < 50 and 
            util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) < 50 and
            thumb_index_dist > 50)

def is_screenshot(landmarks_list, thumb_index_dist):
    return (util.get_angle(landmarks_list[5], landmarks_list[6], landmarks_list[8]) < 50 and 
            util.get_angle(landmarks_list[9], landmarks_list[10], landmarks_list[12]) < 50 and
            thumb_index_dist < 50)

def is_zoom_in(landmarks_list, thumb_index_dist):
    return thumb_index_dist > 100  # Adjust this threshold based on your preference

def is_zoom_out(landmarks_list, thumb_index_dist):
    return thumb_index_dist < 50  # Adjust this threshold based on your preference

def scroll(frame, landmarks_list):
    index_y = landmarks_list[8][1]
    middle_y = landmarks_list[12][1]
    center_y = (index_y + middle_y) / 2

    if center_y < 0.4:
        pyautogui.scroll(30)  # Scroll up
        show_notification(frame, "Scroll Up")
    elif center_y > 0.6:
        pyautogui.scroll(-30) # Scroll down
        show_notification(frame, "Scroll Down")
    else:
        show_notification(frame, "Scrolling Neutral")

def show_notification(frame, action):
    cv2.putText(frame, action, (frame.shape[1]-300, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)
    
def detect_gestures(frame, landmarks_list, processed):
    global gesture_frames
    if len(landmarks_list) >= 21:
        index_finger_tip = find_finger_tip(processed)
        thumb_index_dist = util.get_distance((landmarks_list[4], landmarks_list[8]))
        fingers = fingers_up(landmarks_list)
        # Cursor Movement (only index finger up)
        if fingers == [0,1,0,0,0]:
            move_mouse(index_finger_tip)
            show_notification(frame, "Moving Cursor")
        # Scroll (Index + Middle up) - V Shape
        elif fingers == [0,1,1,0,0]:
            gesture_frames["scroll"] += 1
            if gesture_frames["scroll"] > FRAME_THRESHOLD:
                scroll(frame, landmarks_list)
        else:
            gesture_frames["scroll"] = 0

        # Left Click
        if is_left_click(landmarks_list, thumb_index_dist):
            mouse.press(Button.left)
            mouse.release(Button.left)
            cv2.putText(frame, "Left Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Right Click
        elif is_right_click(landmarks_list, thumb_index_dist):
            mouse.press(Button.right)
            mouse.release(Button.right)
            cv2.putText(frame, "Right Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Double Click
        elif is_double_click(landmarks_list, thumb_index_dist):
            pyautogui.doubleClick()
            cv2.putText(frame, "Double Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        


        # Screenshot
        elif is_screenshot(landmarks_list, thumb_index_dist):
            im1 = pyautogui.screenshot()
            label = random.randint(1, 1000)
            im1.save(f'my_screenshot_{label}.png')
            cv2.putText(frame, "Screenshot", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Zoom In
        elif is_zoom_in(landmarks_list, thumb_index_dist):
            pyautogui.hotkey('ctrl', '+')  # Simulates pressing Ctrl and + for zoom in
            cv2.putText(frame, "Zoom In", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Zoom Out
        elif is_zoom_out(landmarks_list, thumb_index_dist):
            pyautogui.hotkey('ctrl', '-')  # Simulates pressing Ctrl and - for zoom out
            cv2.putText(frame, "Zoom Out", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

def main():
    cap = cv2.VideoCapture(0)
    draw = mp.solutions.drawing_utils

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            processed = hands.process(frameRGB)

            landmarks_list = []

            if processed.multi_hand_landmarks:
                hand_landmarks = processed.multi_hand_landmarks[0]
                draw.draw_landmarks(frame, hand_landmarks, mpHands.HAND_CONNECTIONS)

                for lm in hand_landmarks.landmark:
                    landmarks_list.append((lm.x, lm.y))

            detect_gestures(frame, landmarks_list, processed)

            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
if __name__ == '__main__':
    main()

