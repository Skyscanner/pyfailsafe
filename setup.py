import os

from pip.req import parse_requirements
from setuptools import setup, find_packages


def get_version():
    # Versioning approach adopted as suggested in https://packaging.python.org/en/latest/single_source_version/
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(curr_dir, 'version.txt')) as version_file:
        return version_file.read().strip()


def get_requirements(file):
    requirements = parse_requirements(file, session=False)
    return [str(ir.req) for ir in requirements if not None]


setup(
    name="pyfailsafe",
    version=get_version(),
    url="https://github.com/Skyscanner/pyfailsafe",
    author="Skyscanner",
    author_email="mshell@skyscanner.com",
    description="Failsafe Python implementation",
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=get_requirements("requirements.txt"),
    setup_requires=["pytest-runner"],
    tests_require=get_requirements("requirements_test.txt")
)
