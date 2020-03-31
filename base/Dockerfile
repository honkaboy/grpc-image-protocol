FROM python:latest
RUN pip3 install grpcio grpcio-tools opencv-python numpy

# Generate gRPC libs and make them importable.
ADD proto/image.proto /proto/
RUN mkdir /grpc
RUN python3 -m grpc_tools.protoc -Iproto --python_out=/grpc/ --grpc_python_out=/grpc/ proto/image.proto
ENV PYTHONPATH "${PYTHONPATH}:/grpc/"
