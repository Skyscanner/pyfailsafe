from setuptools import setup
import failsafe
import unasync


setup(
    name="pyfailsafe",
    version=failsafe.__version__,
    url="https://github.com/Skyscanner/pyfailsafe",
    author="Skyscanner",
    author_email="mshell@skyscanner.com",
    description="Simple failure handling. Failsafe implementation in Python",
    packages=[
        "failsafe", "failsafe.aio"
    ],
    license="Apache",
    include_package_data=True,
    platforms="any",
    cmdclass={'build_py': unasync.cmdclass_build_py(rules=[
        unasync.Rule("/aio/", "/sync/"),
    ])},
    install_requires=[]
)
