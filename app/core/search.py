from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import Folder, File
from ..extensions import db

def search():
    query = request.args.get('query', '', type=str)
    folder_id = request.args.get('folder_id', None, type=int)
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

    # Combine queries using union and order by name
    combined_query = folders_query.with_entities(
        Folder.id.label('id'),
        Folder.name.label('name'),
        Folder.created_at.label('created_at'),
        Folder.parent_id.label('parent_id'),
        db.null().label('file_size'),  # Placeholder for file size, null for folders
        db.null().label('mimetype'),  # Placeholder for mimetype, null for folders
        db.literal('folder').label('type')  # Use db.literal for constant value
    ).union_all(
        files_query.with_entities(
            File.id.label('id'),
            File.filename.label('name'),
            File.upload_date.label('created_at'),
            File.parent_id.label('parent_id'),
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
        if item.type == 'file':
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