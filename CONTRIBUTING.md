# Contributing to NetReaper

## Before You Start

Read the README in full. Understand what the project does, how it is
structured, and what the existing modules cover. Check the open issues
to see whether the problem you want to solve is already being worked on.

## Types of Contributions

**Bug reports**
Open an issue using the Bug Report template. Include the operating system
and version, Python version, the exact sequence of menu selections or
commands, and the complete error output. Reports without reproduction steps
will be closed.

**Feature requests**
Open an issue using the Feature Request template. Describe the use case,
not just the implementation. Explain why the feature is appropriate for
a security testing framework targeting isolated lab environments.

**Code contributions**
Fork the repository, create a branch named for the change
(fix/logger-crash, feature/pdf-export), make your changes, and submit
a pull request against main.

## Code Standards

**Style**
Follow PEP 8. Maximum line length is 100 characters. Use flake8 to check:
```
flake8 . --max-line-length=100
```

**Type annotations**
Add type annotations to all new function signatures. Use mypy to verify:
```
mypy . --ignore-missing-imports
```

**Docstrings**
Every module, class, and public function must have a docstring. Docstrings
must describe what the function does, its parameters, return value, and
any exceptions it raises.

**Tests**
Every new function requires at least one test. Tests must not require
network access, root privileges, or external tools. Use mocks for all
subprocess calls and file system interactions that would affect real state.
The test suite must pass with zero failures:
```
python3 -m pytest tests/ -v
```

**Commit messages**
Write in the imperative mood in English:
- "Add PDF export to session logger"
- "Fix KeyboardInterrupt handling in run_command"
- "Remove unused import in wireless module"

Do not use past tense ("Added", "Fixed") or present continuous ("Adding").

## What Will Not Be Merged

- Code that adds attack capabilities intended for use outside isolated test
  environments.
- Code that removes the legal notice from any output.
- Dependencies that are not available in standard Linux package repositories
  or PyPI.
- Tests that require root, network access, or specific hardware.
- Documentation written in any language other than English.
