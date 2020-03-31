from concurrent import futures
import grpc
import cv2
import numpy as np

from image_pb2 import SerializedImage
from image_pb2_grpc import SerializedImageServiceServicer as SerializedImageServiceServicerBase
from image_pb2_grpc import add_SerializedImageServiceServicer_to_server


class MalformedImageError(RuntimeError):
    '''Error to be raised when malformed imaged data is encountered.'''


class SerializedImageServiceServicer(SerializedImageServiceServicerBase):
    """Implements the image server."""
    # This servicer only works with 8-bit-per-channel images.
    IMAGE_BYTE_DEPTH = 1
    NUM_COLOR_CHANNELS = 3

    def __init__(self):
        pass

    @classmethod
    def deserialize_image(cls, image: SerializedImage):
        """ Deserialize image into a numpy image.
        \param image: Serialized image.
        \return image as 2- or 3-D numpy array, depending on color depth.
        """
        # As per the interface image.proto, expect data in 1- or 3- tuples per pixel, row-major.
        # This is how numpy unpacks a buffer by default.
        nparr = np.frombuffer(image.data, np.uint8)

        # Check image integrity before operating on it.
        if image.color == 0:
            num_expected_bytes = image.height * image.width * cls.IMAGE_BYTE_DEPTH
        else:
            num_expected_bytes = image.height * image.width * \
                cls.NUM_COLOR_CHANNELS * cls.IMAGE_BYTE_DEPTH
        num_image_bytes = np.shape(nparr)[0]
        if num_image_bytes != num_expected_bytes:
            raise MalformedImageError(
                f'Image data has {num_image_bytes}, expected {num_expected_bytes}.')

        # Deserialize into a numpy array.
        if image.color == 0:
            img = np.reshape(nparr, (image.height, image.width))
        else:
            # Color images are RGB.
            img = np.reshape(nparr, (image.height, image.width, cls.NUM_COLOR_CHANNELS))

        # At this point, img is either grayscale or RGB in numpy/cv2 format.
        return img

    def RotateImage(self, request, context):
        """ Handler for (serialized) rotation request messages.
        Rotate the image some multiple of 90 deg.
        \param request Rotation request message.
        """
        img = self.deserialize_image(request.image)
        rotated = np.rot90(m=img, k=request.rotation, axes=(0, 1))
        h, w, *_ = np.shape(rotated)
        return SerializedImage(
            color=request.image.color,
            data=rotated.tobytes(),
            height=h,
            width=w)

    def EdgeDetection(self, request, context):
        """ Handler for (serialized) edge detection request messages.
        Run Canny edge detection on an image.
        \param request Edge detection request message.
        """
        img = self.deserialize_image(request.image)
        # Canny edge detection converts to grayscale.
        edges = cv2.Canny(img, 100, 200)
        return SerializedImage(
            color=False,
            data=edges.tobytes(),
            height=request.image.height,
            width=request.image.width)


def serve():
    # Start the image handling gRPC server with several threads & listening on a specific port.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_SerializedImageServiceServicer_to_server(SerializedImageServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
