from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import Folder, File
from app.models.user_model import User, UserSettings
from app.models.search_model import SearchHistory
from ..extensions import db

# File classifications
FILE_CATEGORIES = {
    'pdf': ['application/pdf'],
    'photos_images': ['image/jpeg', 'image/png', 'image/gif'],
    'documents': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'],
    'audio': ['audio/mpeg', 'audio/ogg', 'audio/wav'],
    'video': ['video/mp4', 'video/x-msvideo', 'video/quicktime'],
    'spreadsheets': ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'presentations': ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
    'zip': ['application/zip', 'application/x-tar']
}

def search():
    query = request.args.get('query', '', type=str)
    folder_id = request.args.get('folder_id', None, type=int)
    search_type = request.args.get('type', 'all', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # Number of items per page

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    # Initialize folder and file queries
    folders_query = Folder.query.filter(Folder.name.ilike(f"%{query}%"))
    files_query = File.query.filter(File.filename.ilike(f"%{query}%"))

    if folder_id:
        folders_query = folders_query.filter_by(parent_id=folder_id)
        files_query = files_query.filter_by(parent_id=folder_id)

    # Filter files based on the 'type' argument
    if search_type == 'folder':
        files_query = files_query.filter(False)  # Exclude all files if searching for folders
    elif search_type in FILE_CATEGORIES:
        files_query = files_query.filter(File.mimetype.in_(FILE_CATEGORIES[search_type]))
    elif not search_type == 'all':
        return jsonify({'error': 'Invalid search type'}), 400

    # Combine queries using union and order by name
    combined_query = folders_query.with_entities(
        Folder.id.label('id'),
        Folder.name.label('name'),
        Folder.created_at.label('created_at'),
        Folder.parent_id.label('parent_id'),
        Folder.mount_point.label('mount_point'),  # Include mount_point for folders
        db.null().label('file_size'),  # Placeholder for file size, null for folders
        db.null().label('mimetype'),  # Placeholder for mimetype, null for folders
        db.literal('folder').label('type')  # Use db.literal for constant value
    ).union_all(
        files_query.with_entities(
            File.id.label('id'),
            File.filename.label('name'),
            File.upload_date.label('created_at'),
            File.parent_id.label('parent_id'),
            db.null().label('mount_point'),  # Placeholder for mount_point, null for files
            File.file_size.label('file_size'),
            File.mimetype.label('mimetype'),
            db.literal('file').label('type')  # Use db.literal for constant value
        )
    ).order_by('name')

    # Paginate the combined results
    paginated_results = combined_query.paginate(page=page, per_page=per_page, error_out=False)

    # Format the paginated results
    results = []
    for item in paginated_results.items:
        result = {
            'id': item.id,
            'name': item.name,
            'type': item.type,
            'created_at': item.created_at.isoformat(),  # Convert to ISO format for JSON serialization
            'parent_id': item.parent_id,
        }
        if item.type == 'folder':
            result.update({
                'mount_point': item.mount_point,
            })
        else:  # For files
            result.update({
                'file_size': item.file_size,
                'mimetype': item.mimetype,
            })
        results.append(result)

    return jsonify({
        'results': results,
        'has_next': paginated_results.has_next,
        'has_prev': paginated_results.has_prev,
        'next_page': paginated_results.next_num if paginated_results.has_next else None,
        'prev_page': paginated_results.prev_num if paginated_results.has_prev else None,
        'total_items': paginated_results.total
    })

def list_search(current_user):
    query = request.args.get('query', '', type=str)
    folder_id = request.args.get('folder_id', None, type=int)
    search_type = request.args.get('type', 'all', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # Number of items per page

    if not query:
        return {
            'results': [],
            'has_next': False,
            'has_prev': False,
            'next_page': None,
            'prev_page': None,
            'total_items': 0
        }

    # Initialize folder and file queries
    folders_query = Folder.query.filter(Folder.name.ilike(f"%{query}%"))
    files_query = File.query.filter(File.filename.ilike(f"%{query}%"))

    if folder_id:
        folders_query = folders_query.filter_by(parent_id=folder_id)
        files_query = files_query.filter_by(parent_id=folder_id)

    # Filter files based on the 'type' argument
    if search_type == 'folder':
        files_query = files_query.filter(False)  # Exclude all files if searching for folders
    elif search_type in FILE_CATEGORIES:
        files_query = files_query.filter(File.mimetype.in_(FILE_CATEGORIES[search_type]))
    elif not search_type == 'all':
        return {
            'results': [],
            'has_next': False,
            'has_prev': False,
            'next_page': None,
            'prev_page': None,
            'total_items': 0
        }
    
    existing_search = SearchHistory.query.filter_by(user_id=current_user.id, term=query).first()
    if existing_search:
        # Update the existing search term's timestamp
        existing_search.timestamp = db.func.now()
    else:
        # Add a new search history record
        search_history = SearchHistory(user_id=current_user.id, term=query)
        db.session.add(search_history)
    db.session.commit()

    # Combine queries using union and order by name
    combined_query = folders_query.with_entities(
        Folder.id.label('id'),
        Folder.name.label('name'),
        Folder.created_at.label('created_at'),
        Folder.parent_id.label('parent_id'),
        Folder.mount_point.label('mount_point'),  # Include mount_point for folders
        db.null().label('file_size'),  # Placeholder for file size, null for folders
        db.null().label('mimetype'),  # Placeholder for mimetype, null for folders
        db.literal('folder').label('type')  # Use db.literal for constant value
    ).union_all(
        files_query.with_entities(
            File.id.label('id'),
            File.filename.label('name'),
            File.upload_date.label('created_at'),
            File.parent_id.label('parent_id'),
            db.null().label('mount_point'),  # Placeholder for mount_point, null for files
            File.file_size.label('file_size'),
            File.mimetype.label('mimetype'),
            db.literal('file').label('type')  # Use db.literal for constant value
        )
    ).order_by('name')

    # Paginate the combined results
    paginated_results = combined_query.paginate(page=page, per_page=per_page, error_out=False)

    # Format the paginated results
    results = []
    for item in paginated_results.items:
        result = {
            'id': item.id,
            'name': item.name,
            'type': item.type,
            'created_at': item.created_at.isoformat(),  # Convert to ISO format for JSON serialization
            'parent_id': item.parent_id,
        }
        if item.type == 'folder':
            result.update({
                'mount_point': item.mount_point,
            })
        else:  # For files
            result.update({
                'file_size': item.file_size,
                'mimetype': item.mimetype,
            })
        results.append(result)

    return {
        'results': results,
        'has_next': paginated_results.has_next,
        'has_prev': paginated_results.has_prev,
        'next_page': paginated_results.next_num if paginated_results.has_next else None,
        'prev_page': paginated_results.prev_num if paginated_results.has_prev else None,
        'total_items': paginated_results.total
    }

def get_recent_searches(current_user):
    limit = int(request.args.get('limit', 5))

    recent_searches = SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.timestamp.desc()).limit(limit).all()

    recent_searches_list = [search.term for search in recent_searches]

    if recent_searches_list:
        return jsonify(recent_searches_list)

    return jsonify([]), 404
