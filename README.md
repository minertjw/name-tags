# Name Tag Generator

## Prerequisites

- `python3.12` or higher
- `uv`

### Hints
1. You can install `uv` using `pipx`
> pipx install uv
2. You can install `pipx` on Windows using `scoop`, or your OS package manager if not Windows
> scoop install pipx
3. You can install `scoop` using instructions you get from searching for `scoop`

## Once prerequisites are installed

Create a Python virtual environment and install all requirements
> uv sync --no-python-downloads

Run the application
> uv run python -m nametags


The application opens an integrated browser window, and also
runs a webserver with default address of `http://127.0.0.1:5000`.
Closing the web window will terminate the application and terminal.
