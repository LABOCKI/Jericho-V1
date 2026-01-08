"""
PDF Parser Module
Handles extracting geometric data and metadata from PDF house plans.
"""

import PyPDF2
import pdfplumber
import re
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
from data_structures import (
    Point, Room, Floor, Wall, Door, Window, 
    Elevation, RoofProfile, Building
)


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
        self.building = Building()
    
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
    
    def detect_closed_polygons(self, lines: List[Dict], tolerance: float = 5.0) -> List[List[Tuple[float, float]]]:
        """
        Detect closed polygons from lines that could represent rooms.
        
        Args:
            lines: List of line dictionaries with x0, y0, x1, y1
            tolerance: Distance tolerance for connecting lines
        
        Returns:
            List of polygons, each as a list of (x, y) points
        """
        if not lines:
            return []
        
        # Build a graph of connected line segments
        segments = [(line['x0'], line['y0'], line['x1'], line['y1']) for line in lines]
        
        # Find rectangular patterns (simplified approach)
        rectangles = []
        
        # Group horizontal and vertical lines
        h_lines = []
        v_lines = []
        
        for seg in segments:
            x0, y0, x1, y1 = seg
            length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            
            if length < tolerance:
                continue
            
            # Check if mostly horizontal or vertical
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            
            if dx > dy * 2:  # Horizontal
                h_lines.append((min(x0, x1), max(x0, x1), (y0 + y1) / 2))
            elif dy > dx * 2:  # Vertical
                v_lines.append((min(y0, y1), max(y0, y1), (x0 + x1) / 2))
        
        # Try to find rectangles from horizontal and vertical lines
        for i, h1 in enumerate(h_lines):
            for h2 in h_lines[i+1:]:
                x1_min, x1_max, y1 = h1
                x2_min, x2_max, y2 = h2
                
                if abs(y2 - y1) < tolerance:
                    continue
                
                # Look for matching vertical lines
                for v1 in v_lines:
                    for v2 in v_lines:
                        y1_min, y1_max, x1 = v1
                        y2_min, y2_max, x2 = v2
                        
                        if abs(x2 - x1) < tolerance:
                            continue
                        
                        # Check if they form a rectangle
                        if (abs(x1 - x1_min) < tolerance and abs(x1 - x2_min) < tolerance and
                            abs(x2 - x1_max) < tolerance and abs(x2 - x2_max) < tolerance and
                            abs(y1 - y1_min) < tolerance and abs(y1 - y2_min) < tolerance and
                            abs(y2 - y1_max) < tolerance and abs(y2 - y2_max) < tolerance):
                            
                            rect = [
                                (x1_min, y1),
                                (x1_max, y1),
                                (x1_max, y2),
                                (x1_min, y2)
                            ]
                            
                            # Check if this rectangle is not already added
                            if rect not in rectangles:
                                rectangles.append(rect)
        
        return rectangles
    
    def extract_room_labels(self, page, polygons: List[List[Tuple[float, float]]]) -> Dict[int, str]:
        """
        Extract room labels from text near polygon boundaries.
        
        Args:
            page: pdfplumber page object
            polygons: List of room polygons
        
        Returns:
            Dictionary mapping polygon index to room name
        """
        room_labels = {}
        
        try:
            words = page.extract_words()
            
            for idx, polygon in enumerate(polygons):
                if len(polygon) < 3:
                    continue
                
                # Calculate polygon center
                center_x = sum(p[0] for p in polygon) / len(polygon)
                center_y = sum(p[1] for p in polygon) / len(polygon)
                
                # Find text near the center
                nearest_text = None
                min_distance = float('inf')
                
                for word in words:
                    word_x = (word['x0'] + word['x1']) / 2
                    word_y = (word['y0'] + word['y1']) / 2
                    
                    distance = np.sqrt((word_x - center_x)**2 + (word_y - center_y)**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        nearest_text = word['text']
                
                # Common room keywords
                room_keywords = [
                    'bedroom', 'living', 'kitchen', 'bathroom', 'bath',
                    'dining', 'garage', 'closet', 'hallway', 'entry',
                    'foyer', 'laundry', 'office', 'den', 'family'
                ]
                
                if nearest_text:
                    text_lower = nearest_text.lower()
                    for keyword in room_keywords:
                        if keyword in text_lower:
                            room_labels[idx] = nearest_text
                            break
                    
                    if idx not in room_labels:
                        room_labels[idx] = f"Room {idx + 1}"
                else:
                    room_labels[idx] = f"Room {idx + 1}"
        
        except Exception as e:
            print(f"Error extracting room labels: {e}")
        
        return room_labels
    
    def detect_doors_and_windows(self, lines: List[Dict], threshold: float = 3.0) -> Tuple[List[Door], List[Window]]:
        """
        Detect doors and windows from line patterns and gaps.
        
        Args:
            lines: List of line dictionaries
            threshold: Minimum gap size to consider as door/window
        
        Returns:
            Tuple of (doors, windows) lists
        """
        doors = []
        windows = []
        
        # Simple heuristic: look for short perpendicular lines (door swings)
        # and small gaps in walls
        
        for line in lines:
            length = np.sqrt((line['x1'] - line['x0'])**2 + 
                           (line['y1'] - line['y0'])**2)
            
            # Door swing is typically 2-4 feet
            if 20 < length < 50:  # Assuming PDF units
                mid_x = (line['x0'] + line['x1']) / 2
                mid_y = (line['y0'] + line['y1']) / 2
                
                door = Door(
                    position=Point(mid_x, mid_y),
                    width=length / 10,  # Rough conversion
                    height=7.0
                )
                doors.append(door)
        
        return doors, windows
    
    def parse_floor_label(self, text: str) -> Optional[Tuple[int, str]]:
        """
        Parse floor level from text.
        
        Args:
            text: Text to parse
        
        Returns:
            Tuple of (level_number, floor_name) or None
        """
        patterns = [
            (r'(?i)first\s+floor', 1, 'First Floor'),
            (r'(?i)second\s+floor', 2, 'Second Floor'),
            (r'(?i)third\s+floor', 3, 'Third Floor'),
            (r'(?i)basement', 0, 'Basement'),
            (r'(?i)ground\s+floor', 1, 'Ground Floor'),
            (r'(?i)main\s+floor', 1, 'Main Floor'),
        ]
        
        for pattern, level, name in patterns:
            if re.search(pattern, text):
                return (level, name)
        
        return None
    
    def parse_scale_indicator(self, text: str) -> Optional[float]:
        """
        Parse scale indicator from text (e.g., "1/4\" = 1'-0\"").
        
        Args:
            text: Text to parse
        
        Returns:
            Scale factor or None
        """
        # Pattern for architectural scales like 1/4" = 1'-0"
        pattern = r'(\d+)/(\d+)"\s*=\s*(\d+)\'(?:-(\d+)")?'
        match = re.search(pattern, text)
        
        if match:
            numerator = float(match.group(1))
            denominator = float(match.group(2))
            feet = float(match.group(3))
            inches = float(match.group(4)) if match.group(4) else 0
            
            # Convert to scale factor
            drawing_inches = numerator / denominator
            real_inches = feet * 12 + inches
            scale_factor = real_inches / drawing_inches
            
            return scale_factor
        
        return None
    
    def detect_elevation_view(self, text: str) -> Optional[str]:
        """
        Detect if page contains an elevation view.
        
        Args:
            text: Page text
        
        Returns:
            View name ('front', 'rear', 'left', 'right') or None
        """
        text_lower = text.lower()
        
        views = {
            'front': ['front', 'facade'],
            'rear': ['rear', 'back'],
            'left': ['left', 'side'],
            'right': ['right', 'side']
        }
        
        for view, keywords in views.items():
            for keyword in keywords:
                if keyword in text_lower and 'elevation' in text_lower:
                    return view
        
        return None
    
    def extract_roof_profile(self, lines: List[Dict], page_height: float) -> Optional[RoofProfile]:
        """
        Extract roof profile from elevation lines.
        
        Args:
            lines: List of line dictionaries
            page_height: Height of the page for coordinate conversion
        
        Returns:
            RoofProfile or None
        """
        if not lines:
            return None
        
        # Find lines in upper portion of page (likely roof)
        roof_lines = [
            line for line in lines
            if line['y0'] < page_height * 0.4 or line['y1'] < page_height * 0.4
        ]
        
        if not roof_lines:
            return None
        
        # Extract points from roof lines
        points = []
        for line in roof_lines:
            points.append(Point(line['x0'], line['y0']))
            points.append(Point(line['x1'], line['y1']))
        
        # Sort points by x coordinate
        points.sort(key=lambda p: p.x)
        
        # Remove duplicates
        unique_points = []
        for point in points:
            if not unique_points or abs(point.x - unique_points[-1].x) > 1:
                unique_points.append(point)
        
        if len(unique_points) >= 2:
            return RoofProfile(points=unique_points)
        
        return None
    
    def build_building_structure(self) -> Building:
        """
        Build a complete Building object from parsed data.
        
        Returns:
            Building object with floors, rooms, and elevations
        """
        building = Building()
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text for this page
                    text = page.extract_text() or ""
                    
                    # Check if this is an elevation view
                    elevation_view = self.detect_elevation_view(text)
                    
                    # Extract geometric data
                    lines = page.lines if hasattr(page, 'lines') else []
                    line_dicts = [
                        {
                            'x0': line.get('x0', 0),
                            'y0': line.get('y0', 0),
                            'x1': line.get('x1', 0),
                            'y1': line.get('y1', 0)
                        }
                        for line in lines
                    ]
                    
                    if elevation_view:
                        # Process as elevation
                        roof_profile = self.extract_roof_profile(line_dicts, page.height)
                        elevation = Elevation(
                            view=elevation_view,
                            roof_profile=roof_profile,
                            width=page.width,
                            height=page.height
                        )
                        building.elevations.append(elevation)
                    else:
                        # Process as floor plan
                        floor_info = self.parse_floor_label(text)
                        level = floor_info[0] if floor_info else page_num
                        name = floor_info[1] if floor_info else f"Floor {page_num + 1}"
                        
                        # Detect rooms
                        polygons = self.detect_closed_polygons(line_dicts)
                        room_labels = self.extract_room_labels(page, polygons)
                        
                        # Detect doors and windows
                        doors, windows = self.detect_doors_and_windows(line_dicts)
                        
                        # Create rooms
                        rooms = []
                        for idx, polygon in enumerate(polygons):
                            room_name = room_labels.get(idx, f"Room {idx + 1}")
                            boundary_points = [Point(x, y) for x, y in polygon]
                            
                            room = Room(
                                name=room_name,
                                floor_level=level,
                                boundary_points=boundary_points,
                                doors=[],
                                windows=[]
                            )
                            rooms.append(room)
                        
                        # Create floor
                        floor = Floor(
                            level=level,
                            name=name,
                            rooms=rooms,
                            height=8.0,
                            elevation=level * 8.0
                        )
                        
                        building.floors.append(floor)
                    
                    # Parse scale if present
                    scale = self.parse_scale_indicator(text)
                    if scale:
                        building.scale_factor = scale
        
        except Exception as e:
            print(f"Error building structure: {e}")
        
        # Sort floors by level
        building.floors.sort(key=lambda f: f.level)
        
        self.building = building
        return building
    
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
            'geometric_data': self.extract_geometric_data(),
            'building': self.build_building_structure()
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
