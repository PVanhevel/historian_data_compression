#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

setup
=====

"""

from setuptools import setup, find_packages
from pathlib import Path
import re
from win32api import *

this_directory = Path(__file__).parent
path = this_directory.joinpath("src", "historian_data_compression", "historian_data_compression.py")

long_description = (this_directory / "README.md").read_text()
verstrline = open(path, "rt", encoding="utf8").read()
vsre = r"^__version__ = ['\"]([^'\"]*)['\"]"

VERSION = re.search(vsre, verstrline, re.M).group(1)
DESCRIPTION = "Deadband and swinging door compression of historian data with Python."

setup(
    name="historian_data_compression",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Peter Vanhevel",
    author_email="peter.vanhevel@gmail.com",
    url="https://github.com/PVanhevel/",
    project_urls={
        "Source": "https://github.com/PVanhevel/historian_data_compression",
        "Tracker": "https://github.com/PVanhevel/historian_data_compression/issues",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src", "historian_data_compression": "src/historian_data_compression"},
    install_requires=[],
    keywords=['python', 'historian', 'compression', 'deadband', 'swinging door'],
    license="MIT",
    platforms="any",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development",
        "Typing :: Typed",
        "Programming Language :: Python :: 3",
    ],
)
