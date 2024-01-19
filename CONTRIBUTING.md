# Contributing to ShellGPT
Thank you for considering contributing to ShellGPT! To ensure a smooth and enjoyable experience for everyone, please follow the steps outlined below.

## Find an Issue to Work On
- First, browse the existing issues to find one that interests you. If you find an issue you'd like to work on, assign it to yourself and leave a comment expressing your interest.
- If you have a new feature idea that doesn't have an existing issue, please create a discussion in the "ideas" category using GitHub Discussions. Gather feedback from the community, and if you receive approval from at least a couple of people, create an issue and assign it to yourself.
- If there is an urgent issue, such as a critical bug causing the app to crash, create a pull request immediately.

## Development
ShellGPT is written with strict types, so you'll need to define types. The project uses several linting and testing tools: ruff, mypy, isort, black, and pytest.

### Virtual Environment
Create and activate a virtual environment using Python venv:

```shell
python -m venv env && source ./env/bin/activate
```

### Install Dependencies
Install the necessary dependencies, including development and test dependencies:

```shell
pip install -e ."[dev,test]"
```

### Start Coding
With your environment set up and the issue assigned, you can start working on your solution. Get to know the existing codebase and adhere to the project's coding style and conventions. Write clean, modular, and maintainable code to facilitate understanding and review. Commit your changes frequently to document your progress.

### Testing
**This is a crucial step.** Any changes that implement a new feature or modify existing features should include tests. **Unverified code will not be merged.** These tests should call `sgpt` with defined arguments, capture the output, and verify that the feature works as expected. Refer to the `tests` folder for examples.

### Pull Request
Before creating a pull request, run `scripts/lint.sh` and `scripts/tests.sh` to ensure all linters and tests pass. In your pull request, provide a high-level description of your changes and detailed instructions for testing them, including any necessary commands.

### Code Review
After submitting your pull request, be patient and receptive to feedback from reviewers. Address any concerns they raise and collaborate to refine the code. Together, we can enhance the ShellGPT project.

Thank you once again for your contribution! We're excited to have you join us.