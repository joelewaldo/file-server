from flask import jsonify, request
from ..extensions import db

def update_hashing(current_user):
  data = request.get_json()
  hashing = data.get('hashing', False)
  
  # Update the user's settings
  current_user.settings.hashing = hashing
  db.session.commit()

  return jsonify({'success': True})

def update_preferred_upload_folder(current_user):
  data = request.get_json()
  preferred_upload_folder = data.get('preferred_upload_folder', "")

  current_user.settings.preferred_upload_folder = preferred_upload_folder
  db.session.commit()

  return jsonify({'success': True})