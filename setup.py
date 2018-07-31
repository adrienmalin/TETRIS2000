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
    description="Another Tetris clone. Requires a separate Qt5 library (PyQt5 or PySide2).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adrienmalin/Tetris2000",
    packages=setuptools.find_packages(),
    python_requires='>=3',
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "Tetris2000=Tetris2000.Tetris2000:main"
        ]
    }
)
