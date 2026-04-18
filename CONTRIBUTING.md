# Contributing to OFIP

Thank you for your interest in contributing to the Open Fraud Intelligence Platform (OFIP)!

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest`
5. Format code: `black .`
6. Submit a Pull Request

## Guidelines

- All changes must go through PRs
- Follow PEP 8 style
- Add tests for new features
- Update documentation as needed
- No direct commits to main

## Code of Conduct

Be respectful and inclusive. We follow a code of conduct similar to the Contributor Covenant.

## Reporting Issues

Use GitHub Issues for bugs and feature requests.

## Development Setup

1. Clone the repo
2. Install dependencies: `pip install -e .[dev]`
3. Run the API: `uvicorn api.main:app --reload`