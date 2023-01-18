from setuptools import setup, find_packages

setup(
    name="shell_gpt",
    version="0.2",
    packages=find_packages(),
    py_modules=[
        "sgpt",
        "utils"
    ],
    install_requires=[
        "typer~=0.7.0",
        "requests~=2.28.2",
        "rich==13.1.0",
    ],
    entry_points={
        'console_scripts': [
            'sgpt = sgpt:entry_point'
        ],
    },
    author="Farkhod Sadykov",
    author_email="farkhod.sadykov@gmail.com",
    description="CLI App allows to query OpenAI Chat GPT models using API.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ther1d/shell_gpt",
)
