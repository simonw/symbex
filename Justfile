# Run tests and linters
@default: test lint

# Run pytest with supplied options
@test *options:
  pipenv run pytest {{options}}

# Run linters
@lint:
  pipenv run black . --check
  pipenv run cog --check README.md

# Rebuild docs with cog
@cog:
  pipenv run cog -r README.md

# Apply Black
@black:
  pipenv run black .

# Auto-format and fix things
@fix: cog black
