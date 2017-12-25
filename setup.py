import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "GrblMotors",
    version = "0.1",
    author = "William",
    description = ("Driver interface for using stepper motors with Arduino and GRBL"),
    license = "MIT",
    packages=['GrblMotors'],
    long_description=read('README.md')
)
