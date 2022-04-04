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


def extract_color_features(url: str):
    file_path = __file_path_from_url(url)

    image = Image.open(file_path)
    image_array = np.array(image)
    image_cropped = __crop_image(image_array, 16)

    if image_cropped.size > 0:
        image_array = image_cropped

    colorfulness = __calculate_image_colorfulness(image_array)
    image_array = cv.cvtColor(image_array, cv.COLOR_RGB2HSV)

    h, s, v = cv.split(image_array)
    median_hue = np.median(h)
    median_saturation = np.median(s)
    median_value = np.median(v)
    h_r = h * (np.pi / 90)
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


def __file_path_from_url(url: str):
    return f'./images/{url.split("/")[-2]}.jpg'


def __crop_image(img, tol=0):
    mask = cv.cvtColor(img, cv.COLOR_RGB2GRAY) > tol
    return img[np.ix_(mask.any(1), mask.any(0))]
