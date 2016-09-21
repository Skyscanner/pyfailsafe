from setuptools import setup, find_packages
import failsafe


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
    install_requires=[]
)
