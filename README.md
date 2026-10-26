# Rulewright

**Build reusable transaction categorization rules and apply them offline.**

This beginner-friendly starter app imports a transaction CSV, proposes editable rules using a transparent offline heuristic, then applies the rules deterministically. It is a small MVP scaffold; it does **not** call an AI model yet. Add a hosted open-weight model provider only after the offline workflow is working and documented.

## Features
- CSV upload with common transaction-description column names
- Fictional sample data
- Editable categorization rules
- Deterministic categorization and coverage metric
- CSV and JSON downloads
- Offline operation; no API key needed

## Windows setup
Install Python 3.10 or newer from https://www.python.org/downloads/ and select **Add Python to PATH**.

Open Command Prompt in this folder and run:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown in the terminal, usually http://localhost:8501.

## Tests
```bat
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Privacy
Use fictional data for demos. Do not upload real bank statements to any hosted model or service without understanding its data handling.

## Limitations
- Current rule suggestions use a small hard-coded heuristic, not an AI model.
- Always review suggested categories before using the exported CSV.
- CSV column names vary; unsupported formats may need manual cleanup.

## License
MIT
