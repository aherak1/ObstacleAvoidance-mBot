import cv2
import numpy as np
import yaml
import threading
from flask import Flask, jsonify
import time

command = {'command': ''}
current_reference = None
stop_threads = False
def load_calibration_data(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    camera_matrix = np.array(data['camera_matrix'])
    dist_coeff = np.array(data['dist_coeff'])
    return camera_matrix, dist_coeff

def calculate_focal_length(camera_matrix):
    return camera_matrix[0, 0]
def distance_to_camera(known_width, known_distance, per_width, focal_length):
    return (known_distance * focal_length) / (per_width * known_width)

def detect_color(image, box):
    x, y, w, h = cv2.boundingRect(box)
    roi = image[y:y+h, x:x+w]

    if roi.size == 0:
        print("ROI je prazna, preskoči obrada.")
        return None

    hsv_image = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    color_ranges = {
        'red': ([0, 100, 100], [10, 255, 255]),
        'red2': ([160, 100, 100], [180, 255, 255]),
        'green': ([35, 50, 50], [85, 255, 255]),
        'blue': ([90, 50, 50], [130, 255, 255])
    }

    color_areas = {}

    for color, (lower, upper) in color_ranges.items():
        lower = np.array(lower, dtype="uint8")
        upper = np.array(upper, dtype="uint8")
        mask = cv2.inRange(hsv_image, lower, upper)
        color_areas[color] = np.sum(mask > 0)

    dominant_color = max(color_areas, key=color_areas.get)
    
    if dominant_color == 'red2':
        dominant_color = 'red'

    print(f"Dominantna boja je: {dominant_color}")

    return dominant_color

def send_command(command1):
    global command
    command = command1
    return command1

camera_matrix, dist_coeff = load_calibration_data('calibration_matrix.yaml')

def process_reference(reference, kp_ref, desc_ref, sift, flann, frame, camera_matrix, command_prefix):
    global command
    global current_reference
    global stop_threads

    grayframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kp_frame, desc_frame = sift.detectAndCompute(grayframe, None)

    if desc_frame is None or len(desc_frame) < 2:
        print(f"Nema dovoljno deskriptora za prepoznavanje {command_prefix}.")
        return

    matches = flann.knnMatch(desc_ref, desc_frame, k=2)
    good_points = [m for m, n in matches if m.distance < 0.7 * n.distance]
    img_matches = cv2.drawMatches(reference, kp_ref, grayframe, kp_frame, good_points, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    if len(good_points) >= 4:
        query_pts = np.float32([kp_ref[m.queryIdx].pt for m in good_points]).reshape(-1, 1, 2)
        train_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_points]).reshape(-1, 1, 2)

        matrix, mask = cv2.findHomography(query_pts, train_pts, cv2.RANSAC, 5.0)
        if matrix is not None:
            h, w = reference.shape[:2]
            pts = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, matrix)
            homography = cv2.polylines(frame, [np.int32(dst)], True, (255, 0, 0), 3)

            box = np.int0(dst)
            focal_length = calculate_focal_length(camera_matrix)
            per_width = cv2.norm(box[0] - box[1])
            distance_cm = distance_to_camera(8, 30, per_width, focal_length)
            if distance_cm < 30:
                stop_threads = True
                cv2.drawContours(frame, [box], -1, (0, 255, 0), 2)
                dominant_color = detect_color(frame, box)
                if dominant_color == 'red':
                    command = {'command': 'move_right'}
                elif dominant_color == 'green':
                    command = {'command': 'move_forward'}
                elif dominant_color == 'blue':
                    command = {'command': 'move_left'}
                else:
                    command = {'command': 'move_forward'}
                current_reference = command_prefix
            else:
                send_command({'command': 'move_forward'})
                stop_threads = False
            print(command)
            cv2.putText(frame, f"{distance_cm:.2f} cm",
                        (frame.shape[1] - 200, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        else:
            print(f"Nema dovoljno tačaka za izračunavanje homografije {command_prefix}.")
    else:
        print(f"Nema dovoljno dobrih tačaka za prepoznavanje {command_prefix}.")

def video_stream():
    KNOWN_WIDTH_CM = 8
    KNOWN_DISTANCE_CM = 30

    reference1 = cv2.imread('reference1.jpg', cv2.IMREAD_GRAYSCALE)
    reference2 = cv2.imread('reference2.jpg', cv2.IMREAD_GRAYSCALE)
    reference3 = cv2.imread('reference4.jpg', cv2.IMREAD_GRAYSCALE)

    if reference1 is None or reference2 is None:
        print("Nema referentnih slika.")
        return

    sift = cv2.SIFT_create()
    kp1, desc1 = sift.detectAndCompute(reference1, None)
    kp2, desc2 = sift.detectAndCompute(reference2, None)
    kp3, desc3 = sift.detectAndCompute(reference3, None)

    if desc1 is None or desc2 is None:
        send_command({'command': ''})
        print("Nema dovoljno deskriptora za prepoznavanje.")
        return

    index_params = dict(algorithm=0, trees=5)
    search_params = dict(checks=1000)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Ne može se otvoriti kamera.")
        return

    global stop_threads
    while True:
        ret, frame = cap.read()
        if not ret:
            send_command({'command': ''})
            print("Nema ulaza sa kamere.")
            break

        frame = cv2.resize(frame, (640, 480))

        thread1 = threading.Thread(target=process_reference, args=(reference1, kp1, desc1, sift, flann, frame, camera_matrix, 'reference1'))
        thread2 = threading.Thread(target=process_reference, args=(reference2, kp2, desc2, sift, flann, frame, camera_matrix, 'reference2'))
        thread1.start()
        thread2.start()
        thread2.join()
        thread1.join()
        thread2.join()

        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

app = Flask(__name__)

@app.route('/get_command', methods=['POST'])
def get_command():
    global command
    return jsonify(command), 200

def run_flask():
    app.run(host='0.0.0.0', port=6000)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    video_stream()
