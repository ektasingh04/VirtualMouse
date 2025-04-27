import cv2
import mediapipe as mp
import pyautogui
import util
from pynput.mouse import Button, Controller
import random
import tkinter as tk
import threading
import time

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
# Global variables to track time
start_time = time.time()

# Function to display a temporary notification
def show_notification(message):
    def notification():
        # Create a new root window
        root = tk.Tk()
        root.withdraw()  # Initially hide the window while configuring it
        root.attributes('-topmost', True)  # Make window appear on top of all others
        root.overrideredirect(True)  # Remove window decorations
        
        # Configure the main window background
        root.configure(bg="black")
        
        # Create a frame with a thin black border
        container = tk.Frame(root, bg="black", padx=2, pady=2)
        container.pack(fill="both", expand=True)
        
        # Create the content frame with yellow background
        content = tk.Frame(container, bg="yellow")
        content.pack(fill="both", expand=True)
        
        # Create the label with the message
        label = tk.Label(content, text=message, font=("Arial", 16), bg="yellow", fg="black", padx=20, pady=15)
        label.pack(padx=10, pady=10)
        
        # Pre-calculate size before showing
        root.update_idletasks()
        width = label.winfo_reqwidth() + 40
        height = label.winfo_reqheight() + 30
        
        # Center the window on screen
        x_position = screen_width // 2 - width // 2
        y_position = screen_height // 4  # Position in the top quarter of the screen for less intrusion
        
        # Set the final size and position
        root.geometry(f"{width}x{height}+{x_position}+{y_position}")
        
        # Implement smooth fade-in and fade-out
        def fade_in():
            root.deiconify()  # Show the window
            alpha = 0.0
            while alpha < 1.0:
                root.attributes('-alpha', alpha)
                root.update()
                time.sleep(0.01)
                alpha += 0.1
        
        def fade_out():
            alpha = 1.0
            while alpha > 0.0:
                root.attributes('-alpha', alpha)
                root.update()
                time.sleep(0.01)
                alpha -= 0.1
            root.destroy()
        
        # Execute the fade in
        fade_in()
        
        # Schedule the fade out
        root.after(1200, fade_out)  # Start fading out after 1.2 seconds
        
        root.mainloop()
    
    # Create a new thread to show the notification
    notification_thread = threading.Thread(target=notification)
    notification_thread.daemon = True  # Make thread daemon so it doesn't block program exit
    notification_thread.start()


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

def joints(landmarks_list):
    fingers = []
    # Tip landmarks vs lower joint landmarks
    if landmarks_list[8][1] < landmarks_list[6][1]:  # Index
        fingers.append(1)
    else:
        fingers.append(0)
    if landmarks_list[12][1] < landmarks_list[10][1]:  # Middle
        fingers.append(1)
    else:
        fingers.append(0)
    if landmarks_list[16][1] < landmarks_list[14][1]:  # Ring
        fingers.append(1)
    else:
        fingers.append(0)
    if landmarks_list[20][1] < landmarks_list[18][1]:  # Pinky
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
    fingers = joints(landmarks_list)
    return sum(fingers) == 4  # 4 fingers up

def is_zoom_out(landmarks_list, thumb_index_dist):
    fingers = joints(landmarks_list)
    return sum(fingers) == 3  # 3 fingers up

def scroll(frame, landmarks_list):
    index_y = landmarks_list[8][1]
    middle_y = landmarks_list[12][1]
    center_y = (index_y + middle_y) / 2

    if center_y < 0.4:
        pyautogui.scroll(30)  # Scroll up
        show_action(frame,"Scroll Up")
        show_notification("Scroll Up")

    elif center_y > 0.6:
        pyautogui.scroll(-30) # Scroll down
        show_action(frame,"Scroll Down")
        show_notification("Scroll Down")
    else:
        show_action(frame,"Scrolling Neutral")
        show_notification("Scrolling Neutral")

def show_action(frame, action):
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
            show_action(frame,"Moving Cursor")
            show_notification("Moving Cursor")
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
            #cv2.putText(frame, "Left Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            show_notification("Left Click")

        # Right Click
        elif is_right_click(landmarks_list, thumb_index_dist):
            move_mouse(index_finger_tip)
            show_action(frame,"Moving Cursor")
            show_notification("Moving Cursor")

        # Double Click
        elif is_double_click(landmarks_list, thumb_index_dist):
            pyautogui.doubleClick()
           # cv2.putText(frame, "Double Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            show_notification("Double Click")
        
        # Screenshot
        elif is_screenshot(landmarks_list, thumb_index_dist):
            mouse.press(Button.right)
            mouse.release(Button.right)
            #cv2.putText(frame, "Right Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            show_notification("Right Click")

        # Zoom In
        elif is_zoom_in(landmarks_list, thumb_index_dist):
            pyautogui.hotkey('ctrl', '+')
            #cv2.putText(frame, "Zoom In", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            show_notification("Zoom In")
        # Zoom Out
        elif is_zoom_out(landmarks_list, thumb_index_dist):
            pyautogui.hotkey('ctrl', '-')
            #cv2.putText(frame, "Zoom Out", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            show_notification("Zoom Out")

def check_prolonged_usage():
    elapsed_time = time.time() - start_time
    if elapsed_time >= 30:  # 5 minutes
        show_notification("You may be using the virtual mouse for too long. Take a break!")
    elif elapsed_time >= 3600:  # 60 minutes
        show_notification("Using the virtual mouse for extended periods may cause strain. Please rest!")

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
            check_prolonged_usage()

            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
if __name__ == '__main__':
    main()

