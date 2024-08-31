import os
import io
import shutil
import zipfile
from flask import current_app as app, request, jsonify, send_from_directory, send_file
from app.models.file_model import Folder, File
from ..extensions import db
from PIL import Image
import cv2
import io

def ensure_cache_directory():
  """Ensure that the cache directory exists."""
  if not os.path.exists(app.config.get('CACHE_FOLDER', 'cache')):
    os.makedirs(app.config.get('CACHE_FOLDER', 'cache'))

def scale_image(file_path, target_width=1280, target_height=720):
  """Scale down an image to a specific resolution (720p) and return as a BytesIO object."""
  with Image.open(file_path) as img:
    # Resize the image to fit within the target resolution while maintaining aspect ratio
    img.thumbnail((target_width, target_height), Image.LANCZOS)
    
    # Save image to a BytesIO object
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io

def extract_video_frame(file_path):
  """Extract the first frame of a video and return as a BytesIO object."""
  cap = cv2.VideoCapture(file_path)
  success, frame = cap.read()
  cap.release()
  
  if success:
    # Convert frame to PIL image
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Save image to a BytesIO object
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return img_io
  else:
    return None

def get_thumbnail_path(file_id):
  """Generate the path for the cached thumbnail."""
  return os.path.join(app.config.get('CACHE_FOLDER', 'cache'), f"{file_id}.jpg")

def cache_thumbnail(file_path, file_id):
  """Generate and cache the thumbnail."""
  ensure_cache_directory()
  
  file_extension = os.path.splitext(file_path)[1].lower()
  thumbnail_path = get_thumbnail_path(file_id)
  
  if not os.path.exists(thumbnail_path):
    if file_extension in ['.jpg', '.jpeg', '.png']:  # Handle image files
      img_io = scale_image(file_path)
    elif file_extension in ['.mp4', '.avi', '.mov']:  # Handle video files
      img_io = extract_video_frame(file_path)
    else:
      return None
    
    # Save thumbnail to the cache directory
    with open(thumbnail_path, 'wb') as f:
      f.write(img_io.read())
  
  return thumbnail_path

def add_folder_to_zip(folder, zip_file, base_path=""):
  # Add files in the current folder
  files = File.query.filter_by(parent_id=folder.id).all()
  for file in files:
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filepath)
    arcname = os.path.join(base_path, file.filename)
    zip_file.write(file_path, arcname=arcname)
  
  # Recursively add subfolders
  subfolders = Folder.query.filter_by(parent_id=folder.id).all()
  for subfolder in subfolders:
    folder_path = os.path.join(base_path, subfolder.name)
    add_folder_to_zip(subfolder, zip_file, base_path=folder_path)

def download_file(file_id):
  file = File.query.get(file_id)
  
  if file and os.path.exists(file.filepath):
    return send_file(file.filepath, as_attachment=True, download_name=file.filename)
  else:
    return jsonify({'error': 'File not found'}), 404
  
def download_thumbnail(file_id):
  file = File.query.get(file_id)
    
  if file and os.path.exists(file.filepath):
    thumbnail_path = cache_thumbnail(file.filepath, file_id)
    
    if thumbnail_path and os.path.exists(thumbnail_path):
      return send_file(thumbnail_path, mimetype='image/jpeg', as_attachment=True, download_name=f"{file_id}.jpg")
    else:
      return jsonify({'error': 'Failed to generate thumbnail'}), 500
  else:
    return jsonify({'error': 'File not found'}), 404
  
def download_folder(folder_id):
  folder = Folder.query.get(folder_id)
  
  if not folder:
    return jsonify({'error': 'Folder not found'}), 404
  
  # Create a BytesIO buffer to hold the ZIP data
  buffer = io.BytesIO()
  
  with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    # Recursively add files and folders to the ZIP file
    add_folder_to_zip(folder, zip_file)
  
  buffer.seek(0)
  return send_file(
    buffer,
    as_attachment=True,
    download_name=f"{folder.name}.zip",
    mimetype='application/zip'
  )