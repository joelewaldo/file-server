from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import Folder, File

def search():
    query = request.args.get('query', '', type=str)
    folder_id = request.args.get('folder_id', None, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # Number of items per page

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    # Initialize queries
    folders_query = Folder.query.filter(Folder.name.ilike(f"%{query}%"))
    files_query = File.query.filter(File.filename.ilike(f"%{query}%"))

    if folder_id:
        folders_query = folders_query.filter_by(parent_id=folder_id)
        files_query = files_query.filter_by(parent_id=folder_id)

    # Paginate folders and files separately
    paginated_folders = folders_query.paginate(page=page, per_page=per_page // 2, error_out=False)
    paginated_files = files_query.paginate(page=page, per_page=per_page // 2, error_out=False)

    # Combine and format results
    results = []

    for folder in paginated_folders.items:
        results.append({
            'id': folder.id,
            'name': folder.name,
            'type': 'folder',
            'created_at': folder.created_at, 
            'parent_id': folder.parent_id
        })

    for file in paginated_files.items:
        results.append({
            'id': file.id,
            'name': file.filename,
            'type': 'file',
            'upload_date': file.upload_date,
            'size': file.file_size, 
            'parent_id': file.parent_id
        })

    # You can sort the combined results here if needed
    # results.sort(key=lambda x: x['name'])

    return jsonify({
        'results': results,
        'has_next': paginated_folders.has_next or paginated_files.has_next,
        'has_prev': paginated_folders.has_prev or paginated_files.has_prev,
        'next_page': page + 1 if paginated_folders.has_next or paginated_files.has_next else None,
        'prev_page': page - 1 if paginated_folders.has_prev or paginated_files.has_prev else None,
        'total_items': paginated_folders.total + paginated_files.total
    })