#!/bin/bash

# Set default environment variables
export FLASK_ENV=${FLASK_ENV:-development}
export FLASK_APP=${FLASK_APP:-main.py}

# Optional: Customize the upload folder (comment out if not needed)
export UPLOAD_FOLDER=${UPLOAD_FOLDER:-'/uploads'}

# Optional: Customize the debug mode (comment out if not needed)
export DEBUG=${DEBUG:-True}

# Start the Flask server
echo "Starting Flask server in $FLASK_ENV mode..."
python3 -m flask run