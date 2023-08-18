import platform
import subprocess
import sys
import setuptools
import pathlib
import os

name = "caffa"

current_dir = os.path.abspath(os.curdir)
caffa_dir = os.path.dirname(__file__)
os.chdir(current_dir)

from .client import Client, SessionType
from .object import Object, create_class, create_method_class
from .method import Method
