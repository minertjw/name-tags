# Name Tag Generator

## Quickstart

Requires Python 3.10 or newer.

These setup and launch commands must be entered in a command-line terminal.
Use Terminal on Linux or macOS, or PowerShell on Windows.

From the project directory, create a virtual environment with a recognizable shell prompt:

```bash
python -m venv .venv --prompt name-tags
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Or on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, allow local scripts for the current
PowerShell session and then activate the environment again:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the application:

```bash
python main.py
```

The application opens automatically in your default browser at
`http://127.0.0.1:5000`. Keep the terminal open while using it, and press
`Ctrl+C` in the terminal to stop the server.

An example [template.csv](template.csv) is included with the application. Open
and edit it in Microsoft Excel, replacing the sample rows while keeping the
existing column headers, then upload the saved CSV in the browser.

Generating name tags downloads one print-ready PDF. The individual tag images
are created in temporary storage and deleted automatically after the PDF is built.
