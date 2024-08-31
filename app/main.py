from flask import current_app as app, request, jsonify, send_from_directory, render_template, Blueprint, redirect, url_for
from flask_login import login_required, current_user
import os
from .models.file_model import File, Folder
from .core import upload, delete, download, search as sh, create_folder as cf

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
  return redirect(url_for('auth.login'))

@main_bp.route('/ping')
def test():
  return "pong"

@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
  return upload.upload_file()

@main_bp.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download_file(file_id):
  return download.download_file(file_id)

@main_bp.route('/download_thumbnail/<int:file_id>', methods=['GET'])
@login_required
def download_thumbnail(file_id):
  return download.download_thumbnail(file_id)

@main_bp.route('/download_folder/<int:folder_id>', methods=['GET'])
@login_required
def download_folder(folder_id):
  return download.download_folder(folder_id)

@main_bp.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
  return cf.create_folder()

@main_bp.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
  return delete.delete_file(file_id)

@main_bp.route('/delete_folder/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
  return delete.delete_folder(folder_id)

@main_bp.route('/search', methods=['GET'])
@login_required
def search():
  return sh.search()
  
@main_bp.route('/files', methods=['GET'])
@login_required
def list_files():
  folder_id = request.args.get('folder_id', None, type=int)

  # Initialize stacks
  folder_stack = []
  folder_id_stack = []

  # Handle folder navigation
  folder = None
  if folder_id:
    folder = Folder.query.get(folder_id)
    if folder:
      # Build the folder stack and ID stack
      current_folder = folder
      while current_folder:
        folder_stack.append(current_folder.name)
        folder_id_stack.append(current_folder.id)
        current_folder = Folder.query.get(current_folder.parent_id)
      folder_stack.reverse()
      folder_id_stack.reverse()

      folders_query = Folder.query.filter_by(parent_id=folder_id)
      files_query = File.query.filter_by(parent_id=folder_id)
    else:
      return jsonify({'error': 'Folder not found'}), 404
  else:
    folders_query = Folder.query.filter_by(parent_id=None)
    files_query = File.query.filter_by(parent_id=None)

  # Paginate folders
  all_folders = folders_query.all()

  # Paginate files
  all_files = files_query.all()

  folder_data = list(zip(folder_stack, folder_id_stack))

  return render_template(
    'files.html',
    folders=all_folders,
    files=all_files,
    current_folder=folder,
    folder_data=folder_data
  )

@main_bp.route('/gallery', methods=['GET'])
@login_required
def gallery():
  folder_id = request.args.get('folder_id', None, type=int)
  page = request.args.get('page', 1, type=int)
  per_page = 20  # Number of files per page

  # Initialize stacks
  folder_stack = []
  folder_id_stack = []

  # Handle folder navigation
  folder = None
  if folder_id:
    folder = Folder.query.get(folder_id)
    if folder:
      # Build the folder stack and ID stack
      current_folder = folder
      while current_folder:
        folder_stack.append(current_folder.name)
        folder_id_stack.append(current_folder.id)
        current_folder = Folder.query.get(current_folder.parent_id)
      folder_stack.reverse()
      folder_id_stack.reverse()

      folders_query = Folder.query.filter_by(parent_id=folder_id)
      files_query = File.query.filter_by(parent_id=folder_id)
    else:
      return jsonify({'error': 'Folder not found'}), 404
  else:
    folders_query = Folder.query.filter_by(parent_id=None)
    files_query = File.query.filter_by(parent_id=None)

  all_folders = folders_query.all()

  # Paginate files
  paginated_files = files_query.paginate(page=page, per_page=per_page, error_out=False)

  folder_data = list(zip(folder_stack, folder_id_stack))
  return render_template(
    'files_gallery.html',
    folders=all_folders,
    files=paginated_files.items,
    current_folder=folder,
    folder_data=folder_data,
    page=page
  )

@main_bp.route('/files/<int:file_id>', methods=['GET'])
@login_required
def get_file(file_id):
  file = File.query.get(file_id)
    
  if file and os.path.exists(file.filepath):
    # Determine the file's MIME type
    mime_type = file.mimetype
        
    # Check if it's an image or video
    if mime_type and ('image' in mime_type or 'video' in mime_type):
      return render_template('file_view.html', file=file, mime_type=mime_type, file_extension=file.filename.split('.')[-1].lower())
    else:
      # If it's not an image or video, render a simple page
      return jsonify({'error': 'Unable to view content'}), 404
  else:
    return jsonify({'error': 'File not found'}), 404
  
@main_bp.route('/view/<int:file_id>')
@login_required
def view(file_id):
  file = File.query.get(file_id)
  print(file.filepath)
  return send_from_directory("../" + app.config['UPLOAD_FOLDER'], file.filepath, download_name=file.filename)

@main_bp.route('/folder', methods=['GET'])
@login_required
def get_folder_by_name():
  folder_name = request.args.get('folder_name')
  parent_id = request.args.get('parent_id')

  if not folder_name:
    return jsonify({'error': 'Folder name is required'}), 400
  
  if not parent_id:
    parent_id = None

  folder = Folder.query.filter_by(name=folder_name, parent_id=parent_id).first()

  if folder:
    return jsonify({'folder_id': folder.id})
  else:
    return jsonify({'message': 'Folder not found'}), 200