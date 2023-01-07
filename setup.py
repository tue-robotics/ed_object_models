from setuptools import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=["ed_object_models"],
    package_dir={"": "src"},
    scripts=["scripts"],  # Globally available scripts
)

setup(**d)
