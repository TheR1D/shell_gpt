from setuptools import setup, find_packages


def get_requires():
    requires = []
    with open("requirements.txt") as requirements_file:
        libs = requirements_file.readlines()
        for lib in libs:
            if not lib.startswith("setuptools"):
                requires.append(lib.strip())
    return requires


# pylint: disable=consider-using-with
setup(
    name="shell_gpt",
    version="0.7.3",
    packages=find_packages(),
    install_requires=get_requires(),
    entry_points={
        "console_scripts": ["sgpt = sgpt:cli"],
    },
    author="Farkhod Sadykov",
    author_email="farkhod@sadykov.dev",
    description=(
        "A command-line productivity tool powered by ChatGPT, "
        "will help you accomplish your tasks faster and more efficiently."
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ther1d/shell_gpt",
)
