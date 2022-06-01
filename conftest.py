import os
import pytest
import sys

current_dir = os.path.dirname(__file__)
generated_dir = "generated/"
proto_dir = "protos/"

sys.path.insert(0, os.path.join(current_dir, generated_dir))


def generate_proto_code():
    os.chdir(current_dir)
    if not os.path.exists(generated_dir):
        print("Making directory " + generated_dir)
        os.mkdir(generated_dir)
    os.system("./generate_grpc_classes.sh")


generate_proto_code()
