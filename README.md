# Jericho-V1 - PDF to 3D Model Converter

A Flask-based web application that converts PDF house plans (floor plans and elevations) into scaled 3D models.

## Features

- 📄 **PDF Upload**: Upload house plan PDFs through a user-friendly web interface
- 🔍 **PDF Parsing**: Extract geometric data, dimensions, and text from PDF files using PyPDF2 and pdfplumber
- 🏗️ **3D Model Generation**: Generate scaled 3D models from parsed PDF data using trimesh
- 🎨 **3D Visualization**: Interactive 3D viewer powered by Three.js
- 💾 **Model Export**: Export generated models in OBJ format

## Project Structure

```
/
├── main.py               # Flask app entry point with API routes
├── pdf_parser.py         # PDF parsing logic (PyPDF2, pdfplumber)
├── model_builder.py      # 3D model generation (trimesh)
├── static/
│   └── styles.css        # UI styling
├── templates/
│   ├── index.html        # Main upload interface
│   └── viewer.html       # 3D model viewer (Three.js)
├── requirements.txt      # Python dependencies
└── .gitignore           # Git ignore rules
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/LABOCKI/Jericho-V1.git
cd Jericho-V1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python main.py
```

For development with debug mode (not recommended for production):
```bash
FLASK_DEBUG=true python main.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Upload a PDF house plan and follow the on-screen instructions to:
   - Parse the PDF to extract geometric data
   - Generate a 3D model
   - Visualize the model in the 3D viewer
   - Download the model as an OBJ file

## API Endpoints

- `GET /` - Main application interface
- `POST /upload` - Upload PDF files
- `GET /parse/<filename>` - Parse uploaded PDF
- `GET /generate-model/<filename>` - Generate 3D model from PDF
- `GET /download/<filename>` - Download generated model
- `GET /viewer` - 3D model viewer
- `GET /api/status` - API health check

## Dependencies

- **Flask** - Web framework
- **PyPDF2** - PDF metadata extraction
- **pdfplumber** - PDF text and geometric data extraction
- **numpy** - Numerical computations
- **trimesh** - 3D mesh processing and generation
- **Werkzeug** - WSGI utilities

## Development Status

This is an initial scaffold with placeholder functionality. The current implementation includes:
- ✅ Complete project structure
- ✅ File upload and validation
- ✅ Basic PDF parsing (metadata, text, dimensions, geometric data)
- ✅ Placeholder 3D model generation
- ✅ Interactive 3D viewer
- 🔄 Advanced PDF-to-3D conversion (in development)

## Future Enhancements

- Advanced geometric data extraction from PDFs
- Scale detection and automatic calibration
- Wall, door, and window recognition
- Multi-floor support
- Room labeling and metadata
- Export to additional formats (STL, GLTF)
- Cloud deployment configuration

## Replit Compatibility

This application is fully compatible with Replit. To run on Replit:

### Option 1: Import from GitHub
1. Go to [Replit](https://replit.com/)
2. Click "Create Repl" and select "Import from GitHub"
3. Enter the repository URL: `https://github.com/LABOCKI/Jericho-V1`
4. Replit will automatically detect the configuration and install dependencies
5. Click "Run" to start the application
6. Access the app through Replit's webview

### Option 2: Manual Setup
1. Create a new Python Repl
2. Upload or clone the project files
3. Dependencies will be installed automatically from `requirements.txt`
4. Click "Run" to start the application

The application automatically configures itself for Replit's environment (port and host settings).

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.