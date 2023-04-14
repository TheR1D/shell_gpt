# Contributing to ShellGPT
Thank you for considering contributing to ShellGPT (sgpt)! In order to ensure a smooth and enjoyable experience for everyone, please follow the steps outlined below.

## Find an issue to work on
* First, browse the existing issues to find one that interests you. If you find an issue you would like to work on, assign it to yourself and leave a comment expressing your interest in working on it soon.
* If you have a new feature in mind that doesn't have an existing issue, kindly create a discussion in the "ideas" category using GitHub Discussions. Gather feedback from the community, and if you receive approval from at least a couple of people, create an issue and assign it to yourself.
* If there is an urgent issue, such as a critical bug causing the app to crash, create a pull request right away.

## Developing
> ShellGPT is written using strict types, which means you will need to define types. The project utilizes several linting and testing tools: ruff, mypy, isort, black, and pytest.

### Virtual environment
Create a virtual environment using Python venv and activate it:

```shell
python -m venv env && source ./env/bin/activate
```

### Install dependencies
Install the necessary dependencies, in this case you will need to install the development and test dependencies:

```shell
pip install -e ."[dev,test]"
```
### Start coding
With your environment set up and the issue assigned, you can begin working on your solution. Familiarize yourself with the existing codebase, and follow the project's coding style and conventions. Remember to write clean, modular, and maintainable code, which will make it easier for others to understand and review. As you make progress, commit your changes frequently to keep track of your work. 

### Testing
This is very important step. Every changes that implements a new feature or modifies the logic of existing features should include "integration" tests. These are tests that call `sgpt` with defined arguments, capture the output, and verify that the feature works as expected. See `test_integration.py` for examples. The tests should be easy to read and understand.

### Pull request
Before creating a pull request, ensure that you run `scripts/lint.sh` and `scripts/tests.sh`. All linters and tests should pass. In the pull request, provide a high-level description of your changes and step-by-step instructions on how to test them. Include any necessary commands.

### Code review
Once you've submitted your pull request, it's time for code review. Be patient and open to feedback from the reviewers. Address any concerns they may have and work collaboratively to improve the code. Together, we can make ShellGPT an even better project.

Thank you once again for your contribution! We're excited to have you on board.