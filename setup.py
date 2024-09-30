import os
import pathlib
import setuptools

from subprocess import check_call

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="caffa-python",
    version="1.6.0",
    author="Gaute Lindkvist",
    author_email="lindkvis@gmail.com",
    description="Python bindings for caffa",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lindkvis/caffa-python",
    project_urls={
        "Bug Tracker": "https://github.com/caffa/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: LGPL License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.6",
)
