import cv2 as cv
import mediapipe as mp
import numpy as np
import random
import time

from PIL import Image
from io import BytesIO
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import base64
import tensorflow as tf
import json

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import InputLayer, Conv1D, MaxPooling1D, Flatten, Dense, Conv2D, MaxPooling2D



model = tf.keras.Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(20, 127, 1)),
    MaxPooling2D(pool_size=(2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(pool_size=(2, 2)),
    # LSTM(units=3, input_shape=(1,10)),

    Flatten(),
    Dense(128, activation='relu'),
    Dense(128, activation='relu'),
    Dense(250, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# Load the weights
model.load_weights('/Users/tomasdavola/Downloads/Signly 2/signly/best.weights.h5')

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

asl = {"TV": 0, "after": 1, "airplane": 2, "all": 3, "alligator": 4, "animal": 5, "another": 6, "any": 7, "apple": 8, "arm": 9, "aunt": 10, "awake": 11, "backyard": 12, "bad": 13, "balloon": 14, "bath": 15, "because": 16, "bed": 17, "bedroom": 18, "bee": 19, "before": 20, "beside": 21, "better": 22, "bird": 23, "black": 24, "blow": 25, "blue": 26, "boat": 27, "book": 28, "boy": 29, "brother": 30, "brown": 31, "bug": 32, "bye": 33, "callonphone": 34, "can": 35, "car": 36, "carrot": 37, "cat": 38, "cereal": 39, "chair": 40, "cheek": 41, "child": 42, "chin": 43, "chocolate": 44, "clean": 45, "close": 46, "closet": 47, "cloud": 48, "clown": 49, "cow": 50, "cowboy": 51, "cry": 52, "cut": 53, "cute": 54, "dad": 55, "dance": 56, "dirty": 57, "dog": 58, "doll": 59, "donkey": 60, "down": 61, "drawer": 62, "drink": 63, "drop": 64, "dry": 65, "dryer": 66, "duck": 67, "ear": 68, "elephant": 69, "empty": 70, "every": 71, "eye": 72, "face": 73, "fall": 74, "farm": 75, "fast": 76, "feet": 77, "find": 78, "fine": 79, "finger": 80, "finish": 81, "fireman": 82, "first": 83, "fish": 84, "flag": 85, "flower": 86, "food": 87, "for": 88, "frenchfries": 89, "frog": 90, "garbage": 91, "gift": 92, "giraffe": 93, "girl": 94, "give": 95, "glasswindow": 96, "go": 97, "goose": 98, "grandma": 99, "grandpa": 100, "grass": 101, "green": 102, "gum": 103, "hair": 104, "happy": 105, "hat": 106, "hate": 107, "have": 108, "haveto": 109, "head": 110, "hear": 111, "helicopter": 112, "hello": 113, "hen": 114, "hesheit": 115, "hide": 116, "high": 117, "home": 118, "horse": 119, "hot": 120, "hungry": 121, "icecream": 122, "if": 123, "into": 124, "jacket": 125, "jeans": 126, "jump": 127, "kiss": 128, "kitty": 129, "lamp": 130, "later": 131, "like": 132, "lion": 133, "lips": 134, "listen": 135, "look": 136, "loud": 137, "mad": 138, "make": 139, "man": 140, "many": 141, "milk": 142, "minemy": 143, "mitten": 144, "mom": 145, "moon": 146, "morning": 147, "mouse": 148, "mouth": 149, "nap": 150, "napkin": 151, "night": 152, "no": 153, "noisy": 154, "nose": 155, "not": 156, "now": 157, "nuts": 158, "old": 159, "on": 160, "open": 161, "orange": 162, "outside": 163, "owie": 164, "owl": 165, "pajamas": 166, "pen": 167, "pencil": 168, "penny": 169, "person": 170, "pig": 171, "pizza": 172, "please": 173, "police": 174, "pool": 175, "potty": 176, "pretend": 177, "pretty": 178, "puppy": 179, "puzzle": 180, "quiet": 181, "radio": 182, "rain": 183, "read": 184, "red": 185, "refrigerator": 186, "ride": 187, "room": 188, "sad": 189, "same": 190, "say": 191, "scissors": 192, "see": 193, "shhh": 194, "shirt": 195, "shoe": 196, "shower": 197, "sick": 198, "sleep": 199, "sleepy": 200, "smile": 201, "snack": 202, "snow": 203, "stairs": 204, "stay": 205, "sticky": 206, "store": 207, "story": 208, "stuck": 209, "sun": 210, "table": 211, "talk": 212, "taste": 213, "thankyou": 214, "that": 215, "there": 216, "think": 217, "thirsty": 218, "tiger": 219, "time": 220, "tomorrow": 221, "tongue": 222, "tooth": 223, "toothbrush": 224, "touch": 225, "toy": 226, "tree": 227, "uncle": 228, "underwear": 229, "up": 230, "vacuum": 231, "wait": 232, "wake": 233, "water": 234, "wet": 235, "weus": 236, "where": 237, "white": 238, "who": 239, "why": 240, "will": 241, "wolf": 242, "yellow": 243, "yes": 244, "yesterday": 245, "yourself": 246, "yucky": 247, "zebra": 248, "zipper": 249}
asl_keys = list(asl.keys())
word_list=["TV", "smile", "boat", "thankyou", "no", "head", "up"]
app = Flask(__name__)
CORS(app,resources={r"/*":{"origins":"*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

output=np.zeros((20,126))
indexVector=np.zeros((20,1))
indexVector=np.arange(20)

sentence = random.sample(word_list, 3)
current_word=sentence[0]
current_idx=0
answers = ['incorrect' for _ in range(0, 3)]

@app.route('/')
def index():
    return "WebSocket server running"

@app.route('/hint')
def hint():
    global current_word
    return {"data": current_word}

@socketio.on('connect')
def handle_connect():
    socketio.emit('receive_word', {'message': sentence, 'answers': answers})

@socketio.on('skip_word')
def handle_skip(data):
    global sentence
    global answers
    global current_idx
    global current_word
    current_idx+=1
    if current_idx==3:
        print("All words were signed")
        sentence = random.sample(word_list, 3)
        current_idx=0
        current_word=sentence[0]
    else:
        current_word=sentence[current_idx]
    if answers.count('correct') == len(answers) or answers.count('skipped') == len(answers):
        print("All words were correctly signed")
        sentence = random.sample(word_list, 3)
        current_idx=0
        current_word=sentence[0]
    answers = ['incorrect' for _ in range(0, len(sentence))]
    sentence = data['message']
    answers = data['answers']

@socketio.on('send_frame')
def handle_frame(data):
    global output
    global sentence
    global indexVector
    global answers
    global current_word
    global current_idx
    frame_data = data['frame']
    img_data = base64.b64decode(frame_data.split(',')[1])
    img = Image.open(BytesIO(img_data))
    img = np.array(img)

    frame = cv.cvtColor(img, cv.COLOR_RGB2BGR)

    # frame = cv.flip(frame, 1)

    landmark_coords = [0 for _ in range(126)]

    RGB_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    result = hands.process(RGB_frame)
    y = 0
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            for idx, hand in enumerate(result.multi_handedness):
                if hand.classification[idx - 1].label == "Left":
                    i = 0
                    for landmark in hand_landmarks.landmark:
                        landmark_coords[i] = landmark.x
                        landmark_coords[i + 1] = landmark.y
                        landmark_coords[i + 2] = landmark.z
                        i += 3

                if hand.classification[idx - 1].label == "Right":
                    i = 63
                    for landmark in hand_landmarks.landmark:
                        landmark_coords[i] = landmark.x
                        landmark_coords[i + 1] = landmark.y
                        landmark_coords[i + 2] = landmark.z
                        i += 3
                # if len(landmark_coords) == 126:
                #     landmark_coords = np.insert(landmark_coords, 0, y)
                # else:
                #     landmark_coords[0] = y
                #print(landmark_coords)
                #print(f"Mean: {np.mean(landmark_coords)} SD: {np.std(landmark_coords)}")
                #landmark_coords = landmark_coords[::-1]
                landmark_coords = np.array(landmark_coords)
                output=output[1:,:]
                try:
                    output=np.vstack([output, landmark_coords])
                    output=np.column_stack((indexVector, output))
                    output = output.reshape(1, 20, 127)
                    print("PREDICTING")
                    predictions=model.predict(output)
                    output = output.reshape(20, 127)
                    output=output[:, 1:]
                    print(f'Prediction: {np.max(predictions)} Index: {asl_keys[np.argmax(predictions)]}')

                    # for idx, word in enumerate(sentence):
                    #     if asl_keys[np.argmax(predictions)] == word and answers[idx] != ('correct' or 'skipped'):
                    #         answers[idx] == 'correct'
                    # print(answers)
                    # if answers.count('correct') == len(answers) or answers.count('skipped') == len(answers):
                    #     print("All words were either correctly signed or skipped")
                    #     sentence = random.sample(asl_keys, 3)
                    #     answers = ['incorrect' for _ in range(0, len(sentence))]
                    if asl_keys[np.argmax(predictions)]==current_word:
                        answers[current_idx] = 'correct'
                        current_idx+=1

                        if current_idx==3:
                            print("All words were signed")
                            sentence = random.sample(word_list, 3)
                            current_idx=0
                            current_word=sentence[0]
                        else:
                            current_word=sentence[current_idx]
                        time.sleep(1)
                    if answers.count('correct') == len(answers) or answers.count('skipped') == len(answers) or answers[len(answers) - 1] == 'skipped' or answers.count('incorrect') == 0:
                            print("All words were correctly signed")
                            sentence = random.sample(word_list, 3)
                            current_idx=0
                            current_word=sentence[0]
                            answers = ['incorrect' for _ in range(0, len(sentence))]
                            

                    print(answers)
                    socketio.emit('receive_word', {'message': sentence, 'answers': answers})
                except ValueError:
                    output=np.zeros((20,126))
                    indexVector=np.zeros((20,1))
                    indexVector=np.arange(20)

if __name__ == '__main__':
    socketio.run(app, debug=True, port = 5000)