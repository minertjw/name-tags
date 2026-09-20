# Name Tag Generator

## Development prerequisites

- `python3.12` or higher
- `uv`

### Hints
1. You can install `uv` on Windows using `scoop`, or your OS package manager if not Windows
> scoop install uv
2. You can install `scoop` using [these instructions](https://scoop.sh/)

## Once prerequisites are installed

Create a Python virtual environment and install all requirements
> uv sync --no-python-downloads

Run the application for development
> uv run python -m nametags

Compile the application for distribution
> uv run pyinstaller main.spec


The application opens a self-contained browser window, and also
runs a webserver with default address of `http://127.0.0.1:5000`.
Closing the web window will terminate the application.
