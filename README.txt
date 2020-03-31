gRPC image transformation server/client project

This project provides a server and client to perform "remote" image manipulation. In this small
project, the server and client are on the same localhost, but the project can be easily extended to
perform the manipulation on a remote server. This project also provides a slightly-more-than-minimal
example of using docker-compose to spin up client and server containers simultaneously. (I started
with the example
[here](https://www.freecodecamp.org/news/a-beginners-guide-to-docker-how-to-create-a-client-server-side-with-docker-compose-12c8cf0ae0aa/)
and extended it.

proto/image.proto defines a set of protobuf messages / services related to image transformation and
manipulation that the client can ask for and the server implements. The server / client interface is
implemented with gRPC (https://grpc.io/)


Usage

1. This project relies on docker and docker-compose.
https://docs.docker.com/compose/install/

2. Build the containers, spin up the server and client, run a quick test.
# From project root:
docker-compose build && docker-compose up

3. Interface with the server container and transform as many images as desired.
# We'll restart our client container and transform custom images.
# In order to read and write images after they're transformed, we need to mount a local volume.
# To keep things simple, just copy all the images you want to transform to $PROJECT_ROOT/data.

# In order to interface with the server, we need to let this client container access the localhost
# too.

cp <all your test images> $PROJECT_ROOT/data
# NOTE: PROJECT_ROOT must be an absolute path
docker run -it -v $PROJECT_ROOT/data:/data --network=host image-grpc-client python3 client/image_client.py data/image1.png data/image2.jpg data/image3.jpg


# Open TODOs
- The CLI interface is a little funky. The user has to mount an external drive, then the images are
  written directly to some /data folder.
  # TODO: Make this work nicely with images in arbitrary paths, allow user to specify write
    directory.
