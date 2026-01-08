"""
Model Builder Module
Generates 3D models from parsed PDF data.
"""

import numpy as np
import trimesh
from typing import Dict, List, Any, Tuple, Optional
from data_structures import (
    Building, Floor, Room, Wall, Door, Window,
    Point, Elevation, RoofProfile
)


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
    
    def create_room_walls(self, room: Room, elevation: float = 0.0) -> List[trimesh.Trimesh]:
        """
        Create walls for a room from its boundary points.
        
        Args:
            room: Room object with boundary points
            elevation: Z elevation for the room floor
        
        Returns:
            List of wall meshes
        """
        meshes = []
        boundary = room.boundary_points
        
        if len(boundary) < 2:
            return meshes
        
        for i in range(len(boundary)):
            j = (i + 1) % len(boundary)
            start = boundary[i]
            end = boundary[j]
            
            # Create wall from start to end
            wall_mesh = self.create_wall(
                (start.x * self.scale_factor, start.y * self.scale_factor),
                (end.x * self.scale_factor, end.y * self.scale_factor),
                height=room.height * self.scale_factor,
                thickness=0.5 * self.scale_factor
            )
            
            # Translate to correct elevation
            if wall_mesh.vertices.shape[0] > 0:
                wall_mesh.apply_translation([0, 0, elevation * self.scale_factor])
                meshes.append(wall_mesh)
        
        return meshes
    
    def create_floor_slab(self, room: Room, elevation: float = 0.0, 
                          thickness: float = 0.5) -> trimesh.Trimesh:
        """
        Create a floor slab for a room.
        
        Args:
            room: Room object with boundary points
            elevation: Z elevation for the floor
            thickness: Thickness of the floor slab
        
        Returns:
            Floor slab mesh
        """
        boundary = room.boundary_points
        
        if len(boundary) < 3:
            return trimesh.Trimesh()
        
        try:
            # Create vertices for the floor slab (top and bottom)
            vertices = []
            
            # Bottom vertices
            for point in boundary:
                vertices.append([
                    point.x * self.scale_factor,
                    point.y * self.scale_factor,
                    elevation * self.scale_factor
                ])
            
            # Top vertices
            for point in boundary:
                vertices.append([
                    point.x * self.scale_factor,
                    point.y * self.scale_factor,
                    elevation * self.scale_factor + thickness * self.scale_factor
                ])
            
            vertices = np.array(vertices)
            
            # Create faces
            faces = []
            n = len(boundary)
            
            # Bottom face (triangulate)
            for i in range(1, n - 1):
                faces.append([0, i, i + 1])
            
            # Top face (triangulate)
            for i in range(1, n - 1):
                faces.append([n, n + i + 1, n + i])
            
            # Side faces
            for i in range(n):
                j = (i + 1) % n
                # Two triangles per side
                faces.append([i, j, n + j])
                faces.append([i, n + j, n + i])
            
            faces = np.array(faces)
            
            slab = trimesh.Trimesh(vertices=vertices, faces=faces)
            return slab
            
        except Exception as e:
            print(f"Error creating floor slab: {e}")
            return trimesh.Trimesh()
    
    def create_ceiling(self, room: Room, elevation: float = 0.0) -> trimesh.Trimesh:
        """
        Create a ceiling for a room.
        
        Args:
            room: Room object with boundary points
            elevation: Z elevation for the ceiling
        
        Returns:
            Ceiling mesh
        """
        return self.create_floor_slab(room, elevation + room.height, thickness=0.1)
    
    def create_door_opening(self, door: Door, wall_start: Point, wall_end: Point,
                           elevation: float = 0.0) -> trimesh.Trimesh:
        """
        Create a door opening in a wall.
        
        Args:
            door: Door object
            wall_start: Wall start point
            wall_end: Wall end point
            elevation: Z elevation
        
        Returns:
            Door mesh (frame)
        """
        # Simplified door representation as a frame
        width = door.width * self.scale_factor
        height = door.height * self.scale_factor
        
        pos_x = door.position.x * self.scale_factor
        pos_y = door.position.y * self.scale_factor
        pos_z = elevation * self.scale_factor
        
        # Create a simple box for door frame
        door_mesh = trimesh.creation.box(
            extents=[width, 0.2 * self.scale_factor, height]
        )
        door_mesh.apply_translation([pos_x, pos_y, pos_z + height / 2])
        
        return door_mesh
    
    def create_window_opening(self, window: Window, wall_start: Point, wall_end: Point,
                             elevation: float = 0.0) -> trimesh.Trimesh:
        """
        Create a window opening in a wall.
        
        Args:
            window: Window object
            wall_start: Wall start point
            wall_end: Wall end point
            elevation: Z elevation
        
        Returns:
            Window mesh (frame)
        """
        # Simplified window representation as a frame
        width = window.width * self.scale_factor
        height = window.height * self.scale_factor
        sill_height = window.sill_height * self.scale_factor
        
        pos_x = window.position.x * self.scale_factor
        pos_y = window.position.y * self.scale_factor
        pos_z = elevation * self.scale_factor + sill_height
        
        # Create a simple box for window frame
        window_mesh = trimesh.creation.box(
            extents=[width, 0.1 * self.scale_factor, height]
        )
        window_mesh.apply_translation([pos_x, pos_y, pos_z + height / 2])
        
        return window_mesh
    
    def build_floor(self, floor: Floor) -> List[trimesh.Trimesh]:
        """
        Build all meshes for a single floor.
        
        Args:
            floor: Floor object
        
        Returns:
            List of meshes for this floor
        """
        meshes = []
        
        for room in floor.rooms:
            # Create room walls
            wall_meshes = self.create_room_walls(room, floor.elevation)
            meshes.extend(wall_meshes)
            
            # Create floor slab
            floor_slab = self.create_floor_slab(room, floor.elevation)
            if floor_slab.vertices.shape[0] > 0:
                meshes.append(floor_slab)
            
            # Create ceiling
            ceiling = self.create_ceiling(room, floor.elevation)
            if ceiling.vertices.shape[0] > 0:
                meshes.append(ceiling)
        
        return meshes
    
    def create_roof_from_elevation(self, elevation: Elevation, 
                                   building_width: float,
                                   building_depth: float,
                                   base_height: float) -> List[trimesh.Trimesh]:
        """
        Create roof mesh from elevation profile.
        
        Args:
            elevation: Elevation object with roof profile
            building_width: Width of building
            building_depth: Depth of building
            base_height: Height to start roof from
        
        Returns:
            List of roof meshes
        """
        meshes = []
        
        if not elevation.roof_profile or not elevation.roof_profile.points:
            return meshes
        
        points = elevation.roof_profile.points
        
        # Create a simple gable roof
        if len(points) >= 2:
            # Find the peak
            peak_idx = max(range(len(points)), key=lambda i: points[i].z)
            peak = points[peak_idx]
            
            # Create roof planes
            roof_height = peak.z * self.scale_factor + base_height * self.scale_factor
            
            # Left roof plane
            left_vertices = np.array([
                [0, 0, base_height * self.scale_factor],
                [building_width / 2, 0, roof_height],
                [building_width / 2, building_depth, roof_height],
                [0, building_depth, base_height * self.scale_factor]
            ])
            
            left_faces = np.array([
                [0, 1, 2], [0, 2, 3]
            ])
            
            left_roof = trimesh.Trimesh(vertices=left_vertices, faces=left_faces)
            meshes.append(left_roof)
            
            # Right roof plane
            right_vertices = np.array([
                [building_width / 2, 0, roof_height],
                [building_width, 0, base_height * self.scale_factor],
                [building_width, building_depth, base_height * self.scale_factor],
                [building_width / 2, building_depth, roof_height]
            ])
            
            right_faces = np.array([
                [0, 1, 2], [0, 2, 3]
            ])
            
            right_roof = trimesh.Trimesh(vertices=right_vertices, faces=right_faces)
            meshes.append(right_roof)
        
        return meshes
    
    def build_from_building_structure(self, building: Building) -> trimesh.Trimesh:
        """
        Build a 3D model from a Building structure with multiple floors.
        
        Args:
            building: Building object with floors and elevations
        
        Returns:
            Combined trimesh object
        """
        meshes = []
        
        # Build each floor
        for floor in building.floors:
            floor_meshes = self.build_floor(floor)
            meshes.extend(floor_meshes)
        
        # Calculate building dimensions for roof
        if building.floors and building.floors[0].rooms:
            all_points = []
            for floor in building.floors:
                for room in floor.rooms:
                    for point in room.boundary_points:
                        all_points.append((point.x, point.y))
            
            if all_points:
                xs = [p[0] for p in all_points]
                ys = [p[1] for p in all_points]
                
                building_width = (max(xs) - min(xs)) * self.scale_factor
                building_depth = (max(ys) - min(ys)) * self.scale_factor
                
                # Get the top floor height
                if building.floors:
                    top_floor = max(building.floors, key=lambda f: f.elevation)
                    base_height = top_floor.elevation + top_floor.height
                    
                    # Build roof from elevations
                    for elevation in building.elevations:
                        if elevation.roof_profile:
                            roof_meshes = self.create_roof_from_elevation(
                                elevation, building_width, building_depth, base_height
                            )
                            meshes.extend(roof_meshes)
                            break  # Use first elevation with roof profile
        
        # Combine all meshes
        if meshes:
            # Filter out empty meshes
            valid_meshes = [m for m in meshes if m.vertices.shape[0] > 0]
            
            if valid_meshes:
                combined_mesh = trimesh.util.concatenate(valid_meshes)
                self.mesh = combined_mesh
                return combined_mesh
        
        # Fallback to placeholder if no valid geometry
        print("No valid geometry from building structure. Creating placeholder.")
        return self.create_placeholder_room()
    
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
    
    # Check if we have a Building structure
    building = parsed_data.get('building')
    
    if use_placeholder or not building:
        builder.build_placeholder_model()
    elif building and (building.floors or building.elevations):
        # Build from Building structure
        builder.build_from_building_structure(building)
    elif parsed_data.get('geometric_data', {}).get('lines'):
        # Fall back to geometric data
        builder.build_from_geometric_data()
    else:
        # Last resort: placeholder
        builder.build_placeholder_model()
    
    return builder
