"""
Model Builder Module
Generates 3D models from parsed PDF data.
"""

import numpy as np
import trimesh
from typing import Dict, List, Any, Tuple


class ModelBuilder:
    """
    Builds 3D models from geometric data extracted from PDF house plans.
    """
    
    def __init__(self, parsed_data: Dict[str, Any]):
        """
        Initialize the model builder with parsed PDF data.
        
        Args:
            parsed_data: Dictionary containing parsed geometric and dimension data
        """
        self.parsed_data = parsed_data
        self.mesh = None
        self.scale_factor = 1.0
    
    def set_scale(self, scale_factor: float = 1.0):
        """
        Set the scale factor for the 3D model.
        
        Args:
            scale_factor: Scaling factor for converting PDF units to 3D units
        """
        self.scale_factor = scale_factor
    
    def create_placeholder_room(self, width: float = 10.0, length: float = 12.0, 
                                 height: float = 8.0) -> trimesh.Trimesh:
        """
        Create a placeholder room as a simple box structure.
        This is a starting point for more complex geometry.
        
        Args:
            width: Width of the room in feet
            length: Length of the room in feet
            height: Height of the room in feet
        
        Returns:
            Trimesh object representing the room
        """
        # Scale dimensions
        w = width * self.scale_factor
        l = length * self.scale_factor
        h = height * self.scale_factor
        
        # Create vertices for a box (room)
        vertices = np.array([
            # Floor
            [0, 0, 0],
            [w, 0, 0],
            [w, l, 0],
            [0, l, 0],
            # Ceiling
            [0, 0, h],
            [w, 0, h],
            [w, l, h],
            [0, l, h],
        ])
        
        # Define faces (walls, floor, ceiling)
        faces = np.array([
            # Floor
            [0, 1, 2], [0, 2, 3],
            # Ceiling
            [4, 6, 5], [4, 7, 6],
            # Walls
            [0, 4, 5], [0, 5, 1],  # Front wall
            [1, 5, 6], [1, 6, 2],  # Right wall
            [2, 6, 7], [2, 7, 3],  # Back wall
            [3, 7, 4], [3, 4, 0],  # Left wall
        ])
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        return mesh
    
    def create_wall(self, start: Tuple[float, float], end: Tuple[float, float],
                    height: float = 8.0, thickness: float = 0.5) -> trimesh.Trimesh:
        """
        Create a wall segment from start to end points.
        
        Args:
            start: (x, y) coordinates of wall start
            end: (x, y) coordinates of wall end
            height: Height of the wall
            thickness: Thickness of the wall
        
        Returns:
            Trimesh object representing the wall
        """
        x0, y0 = start
        x1, y1 = end
        
        # Calculate wall direction and perpendicular
        dx = x1 - x0
        dy = y1 - y0
        length = np.sqrt(dx**2 + dy**2)
        
        if length == 0:
            # Degenerate wall, return empty mesh
            return trimesh.Trimesh()
        
        # Normalized perpendicular vector
        px = -dy / length * thickness / 2
        py = dx / length * thickness / 2
        
        # Wall vertices
        vertices = np.array([
            # Bottom
            [x0 - px, y0 - py, 0],
            [x0 + px, y0 + py, 0],
            [x1 + px, y1 + py, 0],
            [x1 - px, y1 - py, 0],
            # Top
            [x0 - px, y0 - py, height],
            [x0 + px, y0 + py, height],
            [x1 + px, y1 + py, height],
            [x1 - px, y1 - py, height],
        ])
        
        # Wall faces
        faces = np.array([
            # Bottom
            [0, 2, 1], [0, 3, 2],
            # Top
            [4, 5, 6], [4, 6, 7],
            # Sides
            [0, 1, 5], [0, 5, 4],
            [1, 2, 6], [1, 6, 5],
            [2, 3, 7], [2, 7, 6],
            [3, 0, 4], [3, 4, 7],
        ])
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        return mesh
    
    def build_from_geometric_data(self) -> trimesh.Trimesh:
        """
        Build a 3D model from the geometric data in parsed_data.
        This is a placeholder that creates walls from detected lines.
        
        Returns:
            Combined trimesh object representing the 3D model
        """
        meshes = []
        
        geometric_data = self.parsed_data.get('geometric_data', {})
        lines = geometric_data.get('lines', [])
        
        # Filter significant lines (walls) - lines longer than threshold
        wall_threshold = 20  # Minimum length for a line to be considered a wall
        
        for line in lines:
            x0, y0 = line['x0'], line['y0']
            x1, y1 = line['x1'], line['y1']
            
            length = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            
            if length > wall_threshold:
                wall = self.create_wall(
                    (x0 * self.scale_factor, y0 * self.scale_factor),
                    (x1 * self.scale_factor, y1 * self.scale_factor),
                    height=8.0 * self.scale_factor
                )
                if wall.vertices.shape[0] > 0:
                    meshes.append(wall)
        
        # If no walls detected, create a placeholder room
        if not meshes:
            print("No significant lines detected. Creating placeholder room.")
            meshes.append(self.create_placeholder_room())
        
        # Combine all meshes
        if meshes:
            combined_mesh = trimesh.util.concatenate(meshes)
            self.mesh = combined_mesh
            return combined_mesh
        
        return trimesh.Trimesh()
    
    def build_placeholder_model(self) -> trimesh.Trimesh:
        """
        Build a simple placeholder 3D model for testing.
        Creates a basic house structure with multiple rooms.
        
        Returns:
            Trimesh object representing a placeholder house
        """
        meshes = []
        
        # Create a few rooms
        room1 = self.create_placeholder_room(width=10, length=12, height=8)
        
        # Translate room2 next to room1
        room2_mesh = self.create_placeholder_room(width=8, length=10, height=8)
        room2_mesh.apply_translation([10 * self.scale_factor, 0, 0])
        
        meshes.extend([room1, room2_mesh])
        
        # Combine all meshes
        combined_mesh = trimesh.util.concatenate(meshes)
        self.mesh = combined_mesh
        return combined_mesh
    
    def export_to_obj(self, output_path: str):
        """
        Export the 3D model to OBJ format.
        
        Args:
            output_path: Path where the OBJ file should be saved
        """
        if self.mesh is None:
            print("No mesh to export. Build a model first.")
            return
        
        try:
            self.mesh.export(output_path)
            print(f"Model exported to {output_path}")
        except Exception as e:
            print(f"Error exporting model: {e}")
    
    def export_to_stl(self, output_path: str):
        """
        Export the 3D model to STL format.
        
        Args:
            output_path: Path where the STL file should be saved
        """
        if self.mesh is None:
            print("No mesh to export. Build a model first.")
            return
        
        try:
            self.mesh.export(output_path)
            print(f"Model exported to {output_path}")
        except Exception as e:
            print(f"Error exporting model: {e}")
    
    def get_model_data(self) -> Dict[str, Any]:
        """
        Get the 3D model data in a format suitable for web visualization.
        
        Returns:
            Dictionary containing vertices and faces
        """
        if self.mesh is None:
            return {'vertices': [], 'faces': []}
        
        return {
            'vertices': self.mesh.vertices.tolist(),
            'faces': self.mesh.faces.tolist()
        }


def build_model(parsed_data: Dict[str, Any], use_placeholder: bool = True) -> ModelBuilder:
    """
    Convenience function to build a 3D model from parsed PDF data.
    
    Args:
        parsed_data: Dictionary containing parsed PDF data
        use_placeholder: If True, creates a placeholder model. Otherwise, builds from data.
    
    Returns:
        ModelBuilder instance with the built model
    """
    builder = ModelBuilder(parsed_data)
    builder.set_scale(0.3048)  # Convert feet to meters
    
    if use_placeholder or not parsed_data.get('geometric_data', {}).get('lines'):
        builder.build_placeholder_model()
    else:
        builder.build_from_geometric_data()
    
    return builder
