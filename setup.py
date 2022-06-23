from setuptools import setup


with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="grater_expectations",
    version="1.0.1",
    description="A grated application of Great Expectations to create greater Expectations",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Jorik Schra",
    author_email="j.c.m.schra@gmail.com",
    url="https://github.com/jschra/grater_expectations",
    install_requires=requirements,
    license=license,
    packages=["."],
    include_package_data=True,
    entry_points={"console_scripts": ["grater = initialize_project:main_program"],},
    python_requires=">=3.8",
)
