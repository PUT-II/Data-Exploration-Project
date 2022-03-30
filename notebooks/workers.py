import os

import cv2 as cv
import numpy as np
import requests
from PIL import Image


def download_and_save(url: str):
    file_path = __file_path_from_url(url)
    if os.path.exists(file_path):
        return

    response = requests.get(url)
    with open(file_path, mode='wb') as file:
        file.write(response.content)


def extract_hsv_features(url: str):
    file_path = __file_path_from_url(url)

    image = Image.open(file_path)
    image_array = np.array(image)
    image_cropped = __crop_image(image_array, 16)
    if image_cropped.size > 0:
        image_array = cv.cvtColor(image_cropped, cv.COLOR_RGB2HSV)

    h, s, v = cv.split(image_array)
    median_hue = np.median(h)
    median_saturation = np.median(s)
    median_value = np.median(v)

    row = {
        'thumbnail_med_hue': median_hue,
        'thumbnail_med_saturation': median_saturation,
        'thumbnail_med_value': median_value
    }

    return url, row


def detect_text(url: str):
    file_path = __file_path_from_url(url)
    image = Image.open(file_path)
    image_array = cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)

    net = cv.dnn.readNet('./frozen_east_text_detection.pb')

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
    scores, _ = net.forward([
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"
    ])

    return url, np.max(scores[0, 0]) >= 0.8


def __file_path_from_url(url: str):
    return f'./images/{url.split("/")[-2]}.jpg'


def __crop_image(img, tol=0):
    mask = cv.cvtColor(img, cv.COLOR_RGB2GRAY) > tol
    return img[np.ix_(mask.any(1), mask.any(0))]
