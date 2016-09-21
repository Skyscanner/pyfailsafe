from setuptools import setup
import failsafe


setup(
    name="pyfailsafe",
    version=failsafe.__version__,
    url="https://github.com/Skyscanner/pyfailsafe",
    author="Skyscanner",
    author_email="mshell@skyscanner.com",
    description="Simple failure handling. Failsafe implementation in Python",
    packages=[
        "failsafe"
    ],
    license="Apache",
    include_package_data=True,
    platforms="any",
    install_requires=[]
)
