import cv2
import numpy as np
import requests
from io import BytesIO

def censor_image(prediction):
    response = requests.get(prediction['source'])
    image_data = response.content
    image_array = np.asarray(bytearray(image_data), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    for part in prediction['exposed_parts']:
        for detection in prediction['exposed_parts'][part]:
            start_point = (detection['left'] - 20, detection['top'] - 20)
            end_point = (detection['right'] + 20, detection['bottom'] + 20)
            cv2.rectangle(image, start_point, end_point, (0, 0, 0), -1)

    _, image_data = cv2.imencode(".jpg", image)
    image_bytes = BytesIO(image_data.tobytes())

    return image_bytes