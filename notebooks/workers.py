import os

import cv2 as cv
import numpy as np
import requests
from PIL import Image
from deepface import DeepFace

__emotion_map = {
    'angry': 1,
    'disgust': 2,
    'fear': 3,
    'happy': 4,
    'sad': 5,
    'surprise': 6,
    'neutral': 7,
}

__race_map = {
    'asian': 1,
    'indian': 2,
    'black': 3,
    'white': 4,
    'middle eastern': 5,
    'latino hispanic': 6
}


def download_and_save(url: str):
    file_path = file_path_from_url(url)
    if os.path.exists(file_path):
        return

    response = requests.get(url)
    with open(file_path, mode='wb') as file:
        file.write(response.content)


def extract_color_features(url: str):
    file_path = file_path_from_url(url)

    image = Image.open(file_path)
    image_array = np.array(image)
    image_cropped = __crop_image(image_array, 16)

    if image_cropped.size > 0:
        image_array = image_cropped

    colorfulness = __calculate_image_colorfulness(image_array)
    image_array = cv.cvtColor(image_array, cv.COLOR_RGB2HSV)

    h, s, v = cv.split(image_array)
    h_r = h * (np.pi / 90)

    median_hue = ((90 / np.pi) * np.arctan2(np.median(np.sin(h_r)), np.median(np.cos(h_r)))) % 180
    median_saturation = np.median(s)
    median_value = np.median(v)
    average_hue = ((90 / np.pi) * np.arctan2(np.mean(np.sin(h_r)), np.mean(np.cos(h_r)))) % 180
    average_saturation = np.mean(s)
    average_value = np.mean(v)

    row = {
        'thumbnail_med_hue': median_hue,
        'thumbnail_med_saturation': median_saturation,
        'thumbnail_med_value': median_value,
        'thumbnail_avg_hue': average_hue,
        'thumbnail_avg_saturation': average_saturation,
        'thumbnail_avg_value': average_value,
        'thumbnail_colorfulness': colorfulness
    }

    return url, row


def extract_face_features(url: str):
    file_path = file_path_from_url(url)
    image_arr = cv.imread(file_path)

    try:
        result = DeepFace.analyze(image_arr,
                                  actions=('emotion', 'age', 'race', 'gender'),
                                  detector_backend='retinaface',
                                  prog_bar=False)
    except ValueError:
        result = {}

    if not result:
        return url, {
            'thumbnail_has_face': False,
            'thumbnail_face_emotion_angry': 0.0,
            'thumbnail_face_emotion_disgust': 0.0,
            'thumbnail_face_emotion_fear': 0.0,
            'thumbnail_face_emotion_happy': 0.0,
            'thumbnail_face_emotion_sad': 0.0,
            'thumbnail_face_emotion_surprise': 0.0,
            'thumbnail_face_emotion_neutral': 0.0,
            'thumbnail_face_dominant_emotion': 0,
            'thumbnail_face_age': 0,
            'thumbnail_face_race_asian': 0.0,
            'thumbnail_face_race_indian': 0.0,
            'thumbnail_face_race_black': 0.0,
            'thumbnail_face_race_white': 0.0,
            'thumbnail_face_race_middle_eastern': 0.0,
            'thumbnail_face_race_latino_hispanic': 0.0,
            'thumbnail_face_dominant_race': 0,
            'thumbnail_face_gender': 0
        }

    row = {
        'thumbnail_has_face': True,
        'thumbnail_face_emotion_angry': result['emotion']['angry'],
        'thumbnail_face_emotion_disgust': result['emotion']['disgust'],
        'thumbnail_face_emotion_fear': result['emotion']['fear'],
        'thumbnail_face_emotion_happy': result['emotion']['happy'],
        'thumbnail_face_emotion_sad': result['emotion']['sad'],
        'thumbnail_face_emotion_surprise': result['emotion']['surprise'],
        'thumbnail_face_emotion_neutral': result['emotion']['neutral'],
        'thumbnail_face_dominant_emotion': __emotion_map[result['dominant_emotion']],
        'thumbnail_face_age': result['age'],
        'thumbnail_face_race_asian': result['race']['asian'],
        'thumbnail_face_race_indian': result['race']['indian'],
        'thumbnail_face_race_black': result['race']['black'],
        'thumbnail_face_race_white': result['race']['white'],
        'thumbnail_face_race_middle_eastern': result['race']['middle eastern'],
        'thumbnail_face_race_latino_hispanic': result['race']['latino hispanic'],
        'thumbnail_face_dominant_race': __race_map[result['dominant_race']],
        'thumbnail_face_gender': 1 if result['gender'] == 'Man' else 2
    }

    return url, row


def detect_text(url: str):
    file_path = file_path_from_url(url)
    image = Image.open(file_path)
    image_array = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)

    net = cv.dnn.readNet('models/frozen_east_text_detection.pb')

    median_b = np.median(image_array[:, :, 0])
    median_g = np.median(image_array[:, :, 1])
    median_r = np.median(image_array[:, :, 2])

    new_W = image.width + 32 - image.width % 32
    new_H = image.height + 32 - image.height % 32
    image_array_input = np.zeros(shape=(new_H, new_W, 3), dtype=np.uint8)

    image_array_input[0:image.height, 0:image.width] = image_array

    blob = cv.dnn.blobFromImage(image_array_input,
                                scalefactor=1.0,
                                size=(new_W, new_H),
                                mean=(median_r, median_g, median_b),
                                swapRB=True,
                                crop=False)
    net.setInput(blob)
    scores, geometry = net.forward([
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"
    ])

    result_mask = scores[0, 0] >= 8
    has_text = np.any(result_mask)
    if not has_text:
        return url, (has_text, 0, 0)

    xData0 = geometry[0, 0, result_mask]
    xData1 = geometry[0, 1, result_mask]
    xData2 = geometry[0, 2, result_mask]
    xData3 = geometry[0, 3, result_mask]
    largest_text_to_image_area_ratio = np.max((xData0 + xData2) * (xData1 + xData3)) / (image.width * image.height)

    text_count = len(scores[0, 0, result_mask])

    return url, (has_text, text_count, largest_text_to_image_area_ratio)


def file_path_from_url(url: str):
    return f'./images/{url.split("/")[-2]}.jpg'


def __calculate_image_colorfulness(image):
    """
    https://pyimagesearch.com/2017/06/05/computing-image-colorfulness-with-opencv-and-python/
    """
    # split the image into its respective RGB components
    (R, G, B) = cv.split(image.astype("float"))
    # compute rg = R - G
    rg = np.absolute(R - G)
    # compute yb = 0.5 * (R + G) - B
    yb = np.absolute(0.5 * (R + G) - B)
    # compute the mean and standard deviation of both `rg` and `yb`
    (rbMean, rbStd) = (np.mean(rg), np.std(rg))
    (ybMean, ybStd) = (np.mean(yb), np.std(yb))
    # combine the mean and standard deviations
    stdRoot = np.sqrt((rbStd ** 2) + (ybStd ** 2))
    meanRoot = np.sqrt((rbMean ** 2) + (ybMean ** 2))
    # derive the "colorfulness" metric and return it
    return stdRoot + (0.3 * meanRoot)


def __crop_image(img, tol=0):
    mask = cv.cvtColor(img, cv.COLOR_RGB2GRAY) > tol
    return img[np.ix_(mask.any(1), mask.any(0))]
