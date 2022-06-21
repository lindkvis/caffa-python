echo "Generating Python GRPC classes"
python -m grpc_tools.protoc -Iprotos --python_out=generated/ --grpc_python_out=generated/ protos/AppInfo.proto
python -m grpc_tools.protoc -Iprotos --python_out=generated/ --grpc_python_out=generated/ protos/FieldService.proto
python -m grpc_tools.protoc -Iprotos --python_out=generated/ --grpc_python_out=generated/ protos/ObjectService.proto
