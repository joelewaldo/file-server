@echo off
SET FLASK_ENV=development
SET FLASK_APP=main.py

REM Optional: Customize the upload folder (comment out if not needed)
REM SET UPLOAD_FOLDER=\uploads

REM Optional: Customize the debug mode (comment out if not needed)
SET DEBUG=True

echo Starting Flask server in %FLASK_ENV% mode...
python -m flask run
