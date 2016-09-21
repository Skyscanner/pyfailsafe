from pip.req import parse_requirements
from setuptools import setup, find_packages
import failsafe


def get_requirements(file):
    requirements = parse_requirements(file, session=False)
    return [str(ir.req) for ir in requirements if not None]

setup(
    name="pyfailsafe",
    version=failsafe.__version__,
    url="https://github.com/Skyscanner/pyfailsafe",
    author="Skyscanner",
    author_email="mshell@skyscanner.com",
    description="Failsafe Python implementation",
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[],
    setup_requires=["pytest-runner"],
    tests_require=get_requirements("requirements_test.txt")
)
