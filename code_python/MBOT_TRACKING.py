import cv2
import numpy as np
def video_stream():
    img = cv2.imread("mymbot.jpg", cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Ne može se učitati referentna slika.")
        return
    
    img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
    cv2.imshow("Reference Image", img)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Ne može se otvoriti kamera.")
        return

    sift = cv2.SIFT_create()
    kp_image, desc_image = sift.detectAndCompute(img, None)
    if desc_image is None:
        print("Ne mogu se pronaći deskriptori u referentnoj slici.")
        return

    index_params = dict(algorithm=0,
                        trees=5)
    search_params = dict(checks=1000)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Nema ulaza sa kamere.")
            break

        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        grayframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        kp_grayframe, desc_grayframe = sift.detectAndCompute(grayframe, None)
        if desc_grayframe is None or desc_image is None or len(desc_grayframe) < 2 or len(desc_image) < 2:
            print("Nema dovoljno deskriptora za prepoznavanje.")
            continue

        matches = flann.knnMatch(desc_image, desc_grayframe, k=2)

        good_points = []
        for match in matches:
            if len(match) < 2:
                continue
            m, n = match
            if m.distance < 0.7 * n.distance:
                good_points.append(m)

        if len(good_points) > 12:
            query_pts = np.float32([kp_image[m.queryIdx].pt for m in good_points]).reshape(-1, 1, 2)
            train_pts = np.float32([kp_grayframe[m.trainIdx].pt for m in good_points]).reshape(-1, 1, 2)
            matrix, mask = cv2.findHomography(query_pts, train_pts, cv2.RANSAC, 5.0)
            
            if matrix is not None:
                h, w = img.shape
                pts = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
                dst = cv2.perspectiveTransform(pts, matrix)
                homography = cv2.polylines(frame, [np.int32(dst)], True, (255, 0, 0), 3)
                cv2.imshow("Homography", homography)
            else:
                cv2.imshow("Homography", grayframe)
        else:
            cv2.imshow("Homography", grayframe)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
video_stream()
