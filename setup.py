#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Tetris2000",
    version="0.2.2",
    author="Adrien Malin",
    author_email="adrien.malin@protonmail.com",
    description="Another Tetris clone",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adrienmalin/Tetris2000",
    packages=setuptools.find_packages(),
    install_requires=[
        'PyQt5',
        'qdarkstyle'
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)