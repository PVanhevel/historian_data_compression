#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

setup
=====

Package installation script.

"""

from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

VERSION = '0.0.8'
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
        "Documentation": "https://swingingdoor.readthedocs.io/en/latest/",
        "Source": "https://github.com/PVanhevel/historian_data_compression",
        "Tracker": "https://github.com/PVanhevel/historian_data_compression/issues",
    },
    packages=find_packages(),
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
