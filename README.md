# KisanSarthi Backend

Flask backend for the KisanSarthi agriculture assistant.

## Setup

1. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Create or verify `.env` contains required API keys:
   - `GEMINI_API_KEY`
   - `WEATHER_API_KEY`
   - `SECRET_KEY`

4. Run the app:
   ```powershell
   python app.py
   ```

## Notes

- `farm_app.db` and `uploads/` are runtime artifacts and are excluded from git.
- `venv/`, `__pycache__/`, and `.env` are also ignored.
