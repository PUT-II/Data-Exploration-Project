import os

import cv2 as cv
import numpy as np
import requests
from PIL import Image


def download_and_save(url_: str):
    file_path = f'./images/{url_.split("/")[-2]}.jpg'
    if os.path.exists(file_path):
        return

    response = requests.get(url_)
    with open(file_path, mode='wb') as file:
        file.write(response.content)


def extract_hsv_features(url: str):
    file_path = f'./images/{url.split("/")[-2]}.jpg'

    image = Image.open(file_path)
    image_array = np.array(image)
    image_cropped = __crop_image(image_array, 16)
    if image_cropped.size > 0:
        image_array = cv.cvtColor(image_cropped, cv.COLOR_RGB2HSV)
    avg_hue = np.median(image_array[:, :, 0])
    avg_saturation = np.median(image_array[:, :, 1])
    avg_value = np.median(image_array[:, :, 2])

    row = {
        'thumbnail_med_hue': avg_hue,
        'thumbnail_med_saturation': avg_saturation,
        'thumbnail_med_value': avg_value
    }

    return url, row


def __crop_image(img, tol=0):
    mask = cv.cvtColor(img, cv.COLOR_RGB2GRAY) > tol
    return img[np.ix_(mask.any(1), mask.any(0))]
