# Name Tag Generator

## Quickstart

Requires Python 3.10 or newer.

These setup and launch commands must be entered in a command-line terminal.
Use Terminal on Linux or macOS, or PowerShell on Windows.

From the project directory, create a virtual environment with a recognisable shell prompt:

```bash
python -m venv .venv --prompt nametags
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

An example [template.csv](template.csv) is included with the application. The
CSV must contain `type,name,header` columns. `type` must be `uones`, `nuches`,
`ausimm`, `nuwie`, `student`, or `industry`. Organization rows use `header` as
the position title and add the matching bundled logo to its left. Student rows
use `header` as the degree. Industry rows use `header` as an image filename;
upload all such images when prompted. `name` is printed in the middle field.
Open the file in Microsoft Excel, replace the sample rows, and upload the saved
CSV in the browser.

Generating name tags downloads one print-ready PDF. The individual tag images
are created in temporary storage and deleted automatically after the PDF is built.
