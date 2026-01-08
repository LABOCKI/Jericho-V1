"""
PDF Parser Module
Handles extracting geometric data and metadata from PDF house plans.
"""

import PyPDF2
import pdfplumber
import re
from typing import Dict, List, Tuple, Any


class PDFParser:
    """
    Parses PDF files to extract geometric data, dimensions, and text.
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF parser with a file path.
        
        Args:
            pdf_path: Path to the PDF file to parse
        """
        self.pdf_path = pdf_path
        self.metadata = {}
        self.pages_data = []
        self.dimensions = []
    
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from the PDF file.
        
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata
                
                self.metadata = {
                    'title': metadata.get('/Title', 'Unknown'),
                    'author': metadata.get('/Author', 'Unknown'),
                    'pages': len(pdf_reader.pages),
                    'creator': metadata.get('/Creator', 'Unknown')
                }
                
                return self.metadata
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
    
    def extract_text(self) -> List[str]:
        """
        Extract text content from all pages of the PDF.
        
        Returns:
            List of text content from each page
        """
        texts = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texts.append(text)
        except Exception as e:
            print(f"Error extracting text: {e}")
        
        return texts
    
    def extract_dimensions(self, texts: List[str] = None) -> List[Dict[str, float]]:
        """
        Extract dimension measurements from text content.
        Looks for patterns like "10'", "15'6\"", "3.5m", etc.
        
        Args:
            texts: Optional list of text strings to parse. If None, extracts from PDF.
        
        Returns:
            List of dictionaries containing dimension data
        """
        if texts is None:
            texts = self.extract_text()
        
        dimensions = []
        
        # Patterns for common dimension formats
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:ft|')",  # Feet
            r"(\d+(?:\.\d+)?)\s*(?:in|\")",  # Inches
            r"(\d+(?:\.\d+)?)\s*m\b",        # Meters
            r"(\d+(?:\.\d+)?)\s*cm\b",       # Centimeters
        ]
        
        for text in texts:
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = float(match.group(1))
                    unit = match.group(0).split()[-1] if ' ' in match.group(0) else match.group(0)[len(match.group(1)):]
                    dimensions.append({
                        'value': value,
                        'unit': unit.strip(),
                        'raw_text': match.group(0)
                    })
        
        self.dimensions = dimensions
        return dimensions
    
    def extract_geometric_data(self) -> Dict[str, Any]:
        """
        Extract geometric data including lines, rectangles, and curves from PDF.
        This is a placeholder for more advanced extraction.
        
        Returns:
            Dictionary containing geometric data
        """
        geometric_data = {
            'lines': [],
            'rectangles': [],
            'curves': []
        }
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract lines
                    lines = page.lines if hasattr(page, 'lines') else []
                    
                    # Extract rectangles
                    rects = page.rects if hasattr(page, 'rects') else []
                    
                    # Extract curves
                    curves = page.curves if hasattr(page, 'curves') else []
                    
                    geometric_data['lines'].extend([
                        {
                            'page': page_num,
                            'x0': line.get('x0', 0),
                            'y0': line.get('y0', 0),
                            'x1': line.get('x1', 0),
                            'y1': line.get('y1', 0)
                        }
                        for line in lines
                    ])
                    
                    geometric_data['rectangles'].extend([
                        {
                            'page': page_num,
                            'x0': rect.get('x0', 0),
                            'y0': rect.get('y0', 0),
                            'x1': rect.get('x1', 0),
                            'y1': rect.get('y1', 0),
                            'width': rect.get('width', 0),
                            'height': rect.get('height', 0)
                        }
                        for rect in rects
                    ])
                    
                    geometric_data['curves'].extend([
                        {
                            'page': page_num,
                            'points': curve.get('points', [])
                        }
                        for curve in curves
                    ])
        
        except Exception as e:
            print(f"Error extracting geometric data: {e}")
        
        return geometric_data
    
    def parse(self) -> Dict[str, Any]:
        """
        Main parsing method that extracts all relevant data from the PDF.
        
        Returns:
            Dictionary containing all extracted data
        """
        result = {
            'metadata': self.extract_metadata(),
            'text': self.extract_text(),
            'dimensions': self.extract_dimensions(),
            'geometric_data': self.extract_geometric_data()
        }
        
        return result


def parse_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary containing all parsed data
    """
    parser = PDFParser(pdf_path)
    return parser.parse()
