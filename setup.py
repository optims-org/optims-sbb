from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as req:
    print(req.read())
    requirements = req.read().splitlines()

setup(
    name='src',
    version='1.0.0',
    description='Optimisation of individual mobility schedules',
    long_description=readme,
    long_description_content_type="text/markdown",
    license_files=('LICENSE',),
    author="Patrick Manser",
    author_email="patr.manser@gmail.com",
    install_requires=requirements,
    packages=find_packages(),
    classifiers=([
        "Programming Language :: Python :: 3.9"
    ]),
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
