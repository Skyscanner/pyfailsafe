# pyfailsafe

Failsafe Python implementation

# THIS IS WORK IN PROGRESS - NOT READY TO BE USED

## Installation

The **pyfailsage** package is hosted on PyPI repository on Artifactory

Take dependency on this library by adding the following lines to your requirements.txt file:

    --extra-index-url https://repository.prod.aws.skyscnr.com/artifactory/api/pypi/pypi/simple
    pyfailsage~=X.X.X

**Make sure that you are connected to VPN when accessing Artifactory. Being on office network is not enough.**
    
## Developing

When making changes to the module it is always a good idea to run everything within a python virtual environment to ensure isolation of dependencies.

    # Python3
    pyvenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r requirements_test.txt

Unit tests are written using pytest and can be run from the root of the project with

    py.test tests/ -v

Coding standards are maintained using the flake8 tool which will run as part of the build process. To run locally simply use:

    flake8 pyfailsafe/ tests/

Merge requests which do not have passing tests or flake8 will not be accepted.
