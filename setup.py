import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "GrblMotors",
    version = "0.1",
    author = "William Holden",
    author_email = "holdenwm@uw.edu",
    description = ("Driver interface for using stepper motors with Arduino and GRBL"),
    license = "MIT",
    # keywords = "example documentation tutorial",
    # url = "http://packages.python.org/an_example_pypi_project",
    packages=['GrblMotors'],
    long_description=read('README.md'),
    # classifiers=[
    #     "Development Status :: 3 - Alpha",
    #     "Topic :: Utilities",
    #     "License :: OSI Approved :: BSD License",
    # ],
)