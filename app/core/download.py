import os
import io
import rawpy
import fitz  # PyMuPDF
import textwrap
import shutil
import zipfile
from flask import current_app as app, request, jsonify, render_template, send_file
from app.models.file_model import Folder, File
from ..extensions import db
from PIL import Image, ImageDraw, ImageFont
import cv2
import io

def ensure_cache_directory():
  """Ensure that the cache directory exists."""
  if not os.path.exists(app.config.get('CACHE_FOLDER', 'cache')):
    os.makedirs(app.config.get('CACHE_FOLDER', 'cache'))

def scale_image(file_path, target_width=1280, target_height=720):
  """Scale down an image to a specific resolution (720p) and return as a BytesIO object."""
  file_extension = os.path.splitext(file_path)[1].lower()
  
  if file_extension == '.arw':
    # Use rawpy to process the ARW file
    with rawpy.imread(file_path) as raw:
      rgb_image = raw.postprocess()
      img = Image.fromarray(rgb_image)
  else:
    # Handle other image types with Pillow
    img = Image.open(file_path)
  
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
  
def generate_pdf_thumbnail(file_path):
  """Generate a thumbnail for a PDF file using PyMuPDF."""
  # Open the PDF file
  pdf_document = fitz.open(file_path)
  
  # Get the first page
  first_page = pdf_document.load_page(0)
  
  # Render the page to an image
  pix = first_page.get_pixmap()
  
  # Convert the image to PIL format
  img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
  
  # Resize the image if necessary
  # img = img.resize((1280, 720), Image.LANCZOS)
  
  # Save the image to a BytesIO object
  img_io = io.BytesIO()
  img.save(img_io, format='JPEG')
  img_io.seek(0)

  return img_io

def generate_text_thumbnail(file_path):
  """Generate a thumbnail for a text file by rendering its contents onto an image without wrapping the text."""
  # Read the content of the text file
  with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

  # Create an image object
  img = Image.new('RGB', (1280, 720), color='white')
  d = ImageDraw.Draw(img)

  # Load a font
  try:
    font = ImageFont.truetype("arial.ttf", 30)
  except IOError:
    font = ImageFont.load_default()

  # Draw the text onto the image
  d.text((10, 10), content, font=font, fill='black')

  # Save the image to a BytesIO object
  img_io = io.BytesIO()
  img.save(img_io, format='JPEG')
  img_io.seek(0)

  return img_io

def get_thumbnail_path(file_id):
  """Generate the path for the cached thumbnail."""
  return os.path.join(app.config.get('CACHE_FOLDER', 'cache'), f"{file_id}.jpg")

def cache_thumbnail(file_path, file_id, mime_type):
  """Generate and cache the thumbnail."""
  ensure_cache_directory()
  
  thumbnail_path = get_thumbnail_path(file_id)
  
  if not os.path.exists(thumbnail_path):
    if mime_type and mime_type.startswith('image/'):  # Handle image files
      img_io = scale_image(file_path)
    elif mime_type and mime_type.startswith('video/'):  # Handle video files
      img_io = extract_video_frame(file_path)
    else:
      return None
    
    # Save thumbnail to the cache directory
    if img_io:
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
    mime_type = file.mimetype
    
    if mime_type == 'application/pdf':
      img_io = generate_pdf_thumbnail(file.filepath)
      if img_io:
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name=f"{file_id}.jpg")
      else:
        return jsonify({'error': 'Failed to generate PDF thumbnail'}), 500
    
    if mime_type.startswith('text/'):
      img_io = generate_text_thumbnail(file.filepath)
      if img_io:
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name=f"{file_id}.jpg")
      else:
        return jsonify({'error': 'Failed to generate text thumbnail'}), 500

    if not (mime_type and (mime_type.startswith('image/') or mime_type.startswith('video/'))):
      return jsonify({'error': 'Thumbnail generation is only supported for images, videos, PDFs, and text files'}), 400

    thumbnail_path = cache_thumbnail(file.filepath, file_id, mime_type)
    
    if thumbnail_path and os.path.exists(thumbnail_path):
      return send_file(thumbnail_path, mimetype='image/jpeg', as_attachment=True, download_name=f"{file_id}.jpg")
    else:
      return jsonify({'error': 'Failed to generate thumbnail'}), 500
  else:
    return jsonify({'error': 'File not found'}), 404
  
def generate_preview(file_path, mime_type, target_width=1920, target_height=1080):
  """Generate a higher resolution preview without caching."""
  if mime_type and mime_type.startswith('image/'):
    # Handle image files
    img_io = scale_image(file_path, target_width, target_height)
  elif mime_type and mime_type.startswith('video/'):
    # Handle video files
    img_io = extract_video_frame(file_path)
  else:
    return None
  
  return img_io

def download_preview(file_id):
  file = File.query.get(file_id)
  
  if file and os.path.exists(file.filepath):
    mime_type = file.mimetype

    if mime_type == 'application/pdf':
      return send_file(file.filepath, mimetype='application/pdf')

    if not (mime_type and (mime_type.startswith('image/') or mime_type.startswith('video/'))):
      return jsonify({'error': 'Preview generation is only supported for images and videos'}), 400

    preview_io = generate_preview(file.filepath, mime_type)
      
    if preview_io:
      return send_file(preview_io, mimetype='image/jpeg', as_attachment=True, download_name=f"{file_id}_preview.jpg")
    else:
      return jsonify({'error': 'Failed to generate preview'}), 500
  else:
      return jsonify({'error': 'File not found'}), 404
  
def download_text_preview(file_id):
  file = File.query.get(file_id)
    
  if file and os.path.exists(file.filepath):
    with open(file.filepath, 'r', encoding='utf-8') as f:
      content = f.read()
    return content, 200, {'Content-Type': 'text/plain'}
  else:
    return jsonify({'error': 'File not found or not a text file'}), 404
  
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