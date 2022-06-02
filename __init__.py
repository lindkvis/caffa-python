from subprocess import check_call
import sys
import setuptools
import pathlib
import os

import grpc
from grpc_tools import protoc

name = "caffa"

current_dir = os.path.abspath(os.curdir)
print (current_dir)
caffa_dir = os.path.dirname(__file__)
generated_dir = "generated/"
proto_dir = "protos/"

sys.path.insert(0, os.path.join(caffa_dir, generated_dir))


def generate_proto_code():
    os.chdir(caffa_dir)
    if not os.path.exists(generated_dir):
        print("Making directory " + generated_dir)
        os.mkdir(generated_dir)
    os.system("./generate_grpc_classes.sh")
    os.chdir(current_dir)


generate_proto_code()

from .client import Client
from .object import Object