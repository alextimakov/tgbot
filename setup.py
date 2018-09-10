import os
from setuptools import setup, find_packages


def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


setup(
    name="src",

    description="src project structure",

    author="Alex Timakov",

    packages=find_packages(exclude=['notebooks']),

    long_description=read('README.md'),
)
