# Contributing to avtools

First off, thank you for considering contributing to our project! Your help is greatly appreciated.

## How to Contribute

### Reporting Bugs

1. Ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/jorgeandrespadilla/avtools/issues).
2. If you're unable to find an open issue addressing the problem, open a new one. Be sure to include:
   - A descriptive title and summary.
   - Steps to reproduce the issue.
   - Any relevant logs, screenshots, or other information.

### Suggesting Enhancements

1. Search the existing [Issues](https://github.com/jorgeandrespadilla/avtools/issues) to see if the enhancement has already been suggested.
2. If not, open a new issue and provide:
   - A clear and descriptive title.
   - A detailed description of the enhancement.
   - Any relevant examples or use cases.

### Submitting Pull Requests

1. Fork the repository.
2. Create a new branch from `main` (or the appropriate base branch).
3. Make your changes.
4. Ensure your code follows the project's coding standards.
5. Write or update tests as necessary.
6. Commit your changes with a clear and descriptive commit message.
7. Push your branch to your forked repository.
8. Open a pull request against the `main` branch of the original repository.

### Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## Additional Information

### Development

This project uses [Poetry](https://python-poetry.org/) for dependency management. If you don't have it installed, follow the instructions [here](https://python-poetry.org/docs/#installation).

To work on the project, follow these steps:
1. Clone the repository.
2. Install the dependencies: `poetry install`.
3. Run the CLI application: `poetry run avtools`.

### Testing

Tests are not mandatory but are highly encouraged and appreciated. To run the tests, use the following command: `poetry run pytest`.

### Base Guidelines

1. After cloning the repository, create a new branch for your changes: `git checkout -b feature/my-new-feature`.
2. Make sure to lint and format your code with `ruff`.
3. Use semantic commit messages: `git commit -m "feat: add new feature"`.
4. Use semantic versioning for your changes. See [semver.org](https://semver.org/) for more information. 
5. A new version will be released based on the changes made, only when changes are merged into `main`. To release a new version, update the version in `pyproject.toml`, `cli.py`, and create a new release (with a tag) on GitHub using the following format: `vX.Y.Z`.

### Troubleshooting

1. When merge conflicts are encountered in `poetry.lock`, run `poetry lock --no-update` to resolve them.

## Getting Help

If you need help, feel free to reach out by opening an issue or contacting the maintainers.

Thank you for your contributions!