from __future__ import print_function

import argparse
import cv2
import grpc
import numpy as np
import os.path
import random
from typing import List

from image_pb2 import SerializedImage, SerializedImageRotateRequest, EdgeDetectionRequest
from image_pb2_grpc import SerializedImageServiceStub


def write_image_to_disk(image: SerializedImage, path: str) -> None:
    """ Write an SerializedImage to a PNG on disk. """
    nparr = np.frombuffer(image.data, np.uint8)

    if image.color == 0:
        img = np.reshape(nparr, (image.height, image.width))
    else:
        # Color images are RGB.
        img = np.reshape(nparr, (image.height, image.width, 3))

    cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def read_image_from_disk(path: str, color=True) -> SerializedImage:
    """ Read an image on disk to a (serialized) SerializedImage object. """
    if color:
        img_bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        # Interface requires RGB ordering.
        img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    else:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    # get image properties.
    h, w, *_ = np.shape(img)
    d = 3 if color else 1

    # Numpy is already row-major, so this nice built-in function puts the data in the order required
    # by the interface.
    data = img.tobytes()
    num_bytes_expected = w * h * d
    assert len(data) == num_bytes_expected, \
        f"Expected {num_bytes_expected} bytes in image {path}, got {len(data)}."
    return SerializedImage(color=color, data=data, height=h, width=w)


def rotate_image(stub: SerializedImageServiceStub, image: SerializedImage) -> SerializedImage:
    """ Rotate an image using the gRPC request. """
    rotation_request = SerializedImageRotateRequest(
        rotation=SerializedImageRotateRequest.ONE_EIGHTY_DEG, image=image)
    rotated_image = stub.RotateImage(rotation_request)
    return rotated_image


def detect_edge(stub: SerializedImageServiceStub, image: SerializedImage) -> SerializedImage:
    """ Run edge detection on an image using the gRPC request. """
    edge_detection_request = EdgeDetectionRequest(image=image)
    detected_edges = stub.EdgeDetection(edge_detection_request)
    return detected_edges


def transform_images(images: List[str]):
    """ Transform images, writing them to similar locations on disk. """
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = SerializedImageServiceStub(channel)
        for image in images:
            # Find, deserialize each image.
            assert os.path.isfile(image), f"Cannot find file {image}"
            nl_image = read_image_from_disk(image)

            # Rotate
            rotated = rotate_image(stub, nl_image)
            rotated_filename = image + '_rotated.png'
            write_image_to_disk(rotated, rotated_filename)
            print("wrote " + rotated_filename)

            # Edge detect
            edges = detect_edge(stub, nl_image)
            edge_filename = image + '_edges.png'
            write_image_to_disk(edges, edge_filename)
            print("wrote " + edge_filename)


if __name__ == '__main__':
    # Defines a CLI that can be used to pass multiple images for transformation.

    # https://stackoverflow.com/questions/15203829/python-argparse-file-extension-checking#15203955
    def file_choices(choices, filename):
        ext = os.path.splitext(filename)[1][1:]
        if ext not in choices:
            parser.error(f"{filename} not supported, must be of extension {choices}")
        return filename

    parser = argparse.ArgumentParser(description='Process some images via RPC.')
    parser.add_argument('images', type=lambda s: file_choices(("png", "jpg"), s), nargs='+')
    args = parser.parse_args()
    transform_images(args.images)
