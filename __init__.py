name = "caffa"

import os
import pathlib
import setuptools
import sys

from subprocess import check_call

import grpc
from grpc_tools import protoc

current_dir = os.path.dirname(__file__)
generated_dir = "generated/"
proto_dir = "protos/"

sys.path.insert(0, os.path.join(current_dir, generated_dir))

def generate_proto_code():
    os.chdir(current_dir)
    os.system("./generate_grpc_classes.sh")

generate_proto_code()

from .client import Client
from .object import Object
