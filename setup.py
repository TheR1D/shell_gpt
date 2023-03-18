from setuptools import setup, find_packages

# pylint: disable=consider-using-with
setup(
    name="shell_gpt",
    version="0.7.3",
    packages=find_packages(),
    install_requires=[
        "typer~=0.7.0",
        "requests~=2.28.2",
        "rich==13.3.1",
        "distro~=1.8.0",
    ],
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
