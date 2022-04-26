#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

setup
=====

"""

from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

VERSION = '0.0.14'
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
    keywords=['python', 'historian', 'compression', 'deadband', 'swing door'],
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
