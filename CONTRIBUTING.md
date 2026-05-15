# Contributing to ChuckleNet

Thank you for your interest in contributing!

## How to Contribute

1. **Fork the repository** and create your branch from `main`
2. **Write tests** for any new functionality — aim for parity with existing coverage
3. **Ensure tests pass**: `python -m pytest tests/ -v`
4. **Keep commits atomic** — one feature or fix per commit
5. **Write clear commit messages** using conventional commits format:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation only
   - `test:` test additions
   - `refactor:` code restructure with no behavior change

## Development Setup

```bash
git clone https://github.com/Das-rebel/ChuckleNet.git
cd ChuckleNet
pip install -r requirements.txt
python -m pytest tests/  # verify setup
```

## Code Style

- Python: follow PEP 8, max line length 120
- Use type hints where possible
- Docstrings for all public functions and classes

## Reporting Issues

- Search existing issues first
- For bugs: include Python version, PyTorch version, and minimal reproduction case
- For features: describe the use case and expected behavior

## Pull Request Process

1. Update documentation for any changed interfaces
2. Add/update tests for new functionality
3. PRs require review before merge — expect feedback within 48h

## Questions?

Open a Discussion at https://github.com/Das-rebel/ChuckleNet/discussions