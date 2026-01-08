"""
Main Flask Application
Entry point for the PDF to 3D model conversion app.
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import json

from pdf_parser import parse_pdf
from model_builder import build_model

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Args:
        filename: Name of the file to check
    
    Returns:
        Boolean indicating if file is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """
    Render the main page with file upload form.
    """
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle PDF file upload and initiate processing.
    
    Returns:
        JSON response with upload status and file information
    """
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
    
    # Save the file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({
        'message': 'File uploaded successfully',
        'filename': filename,
        'filepath': filepath
    }), 200


@app.route('/parse/<filename>', methods=['GET'])
def parse_file(filename):
    """
    Parse the uploaded PDF file and extract data.
    
    Args:
        filename: Name of the file to parse
    
    Returns:
        JSON response with parsed data
    """
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Parse the PDF
        parsed_data = parse_pdf(filepath)
        
        return jsonify({
            'message': 'PDF parsed successfully',
            'data': {
                'metadata': parsed_data.get('metadata', {}),
                'text_length': len(parsed_data.get('text', [])),
                'dimensions_count': len(parsed_data.get('dimensions', [])),
                'lines_count': len(parsed_data.get('geometric_data', {}).get('lines', [])),
                'rectangles_count': len(parsed_data.get('geometric_data', {}).get('rectangles', []))
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Error parsing PDF: {str(e)}'}), 500


@app.route('/generate-model/<filename>', methods=['GET'])
def generate_model(filename):
    """
    Generate a 3D model from the parsed PDF data.
    
    Args:
        filename: Name of the PDF file to generate model from
    
    Returns:
        JSON response with 3D model data
    """
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Parse the PDF
        parsed_data = parse_pdf(filepath)
        
        # Build the 3D model
        # Use placeholder model by default for initial scaffold
        builder = build_model(parsed_data, use_placeholder=True)
        
        # Get model data for visualization
        model_data = builder.get_model_data()
        
        # Export to OBJ file
        obj_filename = filename.rsplit('.', 1)[0] + '.obj'
        obj_filepath = os.path.join(app.config['UPLOAD_FOLDER'], obj_filename)
        builder.export_to_obj(obj_filepath)
        
        return jsonify({
            'message': '3D model generated successfully',
            'model_data': model_data,
            'obj_file': obj_filename
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Error generating model: {str(e)}'}), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Download a generated model file.
    
    Args:
        filename: Name of the file to download
    
    Returns:
        File download response
    """
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True)


@app.route('/viewer')
def viewer():
    """
    Render the 3D model viewer page.
    """
    model_file = request.args.get('model', '')
    return render_template('viewer.html', model_file=model_file)


@app.route('/api/status', methods=['GET'])
def status():
    """
    Health check endpoint.
    
    Returns:
        JSON response with API status
    """
    return jsonify({
        'status': 'online',
        'message': 'PDF to 3D Model API is running'
    }), 200


if __name__ == '__main__':
    # Run the Flask app
    # Debug mode should only be enabled in development, not production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Support Replit environment variables
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    print("Starting PDF to 3D Model Conversion App...")
    print(f"Visit http://localhost:{port} to access the application")
    if debug_mode:
        print("WARNING: Running in DEBUG mode. This should NOT be used in production!")
    
    app.run(host=host, port=port, debug=debug_mode)
