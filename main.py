import streamlit as st
import cv2
import mediapipe as mp
import time

# ------------------------------------------
# Keyboard Layout
# ------------------------------------------
keys = [
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
]

def draw_keyboard(frame, finger_pos, last_pressed_key):
    key_w, key_h = 55, 55
    padding = 8
    h, w, _ = frame.shape
    y_base = int(h / 2) - 130
    pressed_key = None

    for row_idx, row in enumerate(keys):
        row_width = len(row) * (key_w + padding)
        x_start = (w - row_width) // 2
        y = y_base + row_idx * (key_h + padding)

        for i, key in enumerate(row):
            x = x_start + i * (key_w + padding)

            is_pressed = False
            if finger_pos:
                fx, fy = finger_pos
                if x < fx < x + key_w and y < fy < y + key_h:
                    pressed_key = key
                    is_pressed = True

            color = (0, 0, 255) if key == last_pressed_key else (0, 255, 0)
            thickness = 2 if is_pressed else 1
            cv2.rectangle(frame, (x, y), (x + key_w, y + key_h), color, thickness)
            cv2.putText(frame, key, (x + 15, y + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

    return frame, pressed_key

# ------------------------------------------
# Streamlit App
# ------------------------------------------
st.set_page_config(page_title="Virtual Keyboard", layout="centered")

st.title("🖐 Virtual Keyboard with Hand Gestures")
st.markdown("Control a keyboard using your index finger gesture! ✨")

placeholder = st.empty()
typed_placeholder = st.empty()

# Mediapipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

typed_text = ''
last_pressed_key = None
last_press_time = 0
key_cooldown = 1.0
previous_key = None

# ✅ Single checkbox for start/stop
run = st.checkbox("Enable Virtual Keyboard")

if run:
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    time.sleep(2)

    while True:
        ret, frame = cap.read()
        if not ret:
            st.warning("Could not access webcam.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        finger_pos = None
        index_finger_open = False

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                h, w, _ = frame.shape
                tip = hand_landmarks.landmark[8]   # Index fingertip
                pip = hand_landmarks.landmark[6]   # Joint below tip

                tip_x, tip_y = int(tip.x * w), int(tip.y * h)
                pip_y = int(pip.y * h)

                # Draw red dot at index tip
                cv2.circle(frame, (tip_x, tip_y), 10, (0, 0, 255), cv2.FILLED)

                # ✅ Finger open only if tip clearly above joint
                if tip_y < pip_y - 10:
                    finger_pos = (tip_x, tip_y)
                    index_finger_open = True
                else:
                    index_finger_open = False

        frame, current_key = draw_keyboard(frame, finger_pos, last_pressed_key)
        current_time = time.time()

        # ✅ Register key only if finger open, new key, and cooldown passed
        if index_finger_open and current_key and (current_key != previous_key):
            if current_time - last_press_time > key_cooldown:
                typed_text += current_key.lower()
                last_pressed_key = current_key
                last_press_time = current_time

        previous_key = current_key

        typed_placeholder.markdown(f"### ✍ Typed Text: {typed_text}")
        placeholder.image(frame, channels="BGR")

        # ✅ Stop loop if checkbox unchecked
        if not st.session_state.get("Enable Virtual Keyboard", run):
            break

    cap.release()
    cv2.destroyAllWindows()
