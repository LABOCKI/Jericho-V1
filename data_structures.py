"""
Data Structures Module
Defines classes for representing building components extracted from PDFs.
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Point:
    """2D or 3D point."""
    x: float
    y: float
    z: float = 0.0
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)
    
    def to_2d_tuple(self) -> Tuple[float, float]:
        """Convert to 2D tuple."""
        return (self.x, self.y)


@dataclass
class Door:
    """Represents a door in a building."""
    position: Point
    width: float
    height: float = 7.0  # Default door height in feet
    wall_index: Optional[int] = None
    
    def __post_init__(self):
        """Initialize with default height if not specified."""
        if self.height is None:
            self.height = 7.0


@dataclass
class Window:
    """Represents a window in a building."""
    position: Point
    width: float
    height: float = 4.0  # Default window height in feet
    sill_height: float = 3.0  # Height from floor to window sill
    wall_index: Optional[int] = None
    
    def __post_init__(self):
        """Initialize with default dimensions if not specified."""
        if self.height is None:
            self.height = 4.0
        if self.sill_height is None:
            self.sill_height = 3.0


@dataclass
class Wall:
    """Represents a wall segment."""
    start: Point
    end: Point
    thickness: float = 0.5
    height: float = 8.0
    is_exterior: bool = False
    
    def length(self) -> float:
        """Calculate wall length."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return np.sqrt(dx**2 + dy**2)
    
    def angle(self) -> float:
        """Calculate wall angle in radians."""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return np.arctan2(dy, dx)


@dataclass
class Room:
    """Represents a room in a building."""
    name: str
    floor_level: int
    boundary_points: List[Point]
    doors: List[Door] = field(default_factory=list)
    windows: List[Window] = field(default_factory=list)
    area: float = 0.0
    height: float = 8.0
    
    def __post_init__(self):
        """Calculate area if not provided."""
        if self.area == 0.0 and len(self.boundary_points) >= 3:
            self.area = self._calculate_area()
    
    def _calculate_area(self) -> float:
        """Calculate room area using shoelace formula."""
        n = len(self.boundary_points)
        if n < 3:
            return 0.0
        
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.boundary_points[i].x * self.boundary_points[j].y
            area -= self.boundary_points[j].x * self.boundary_points[i].y
        
        return abs(area) / 2.0


@dataclass
class Floor:
    """Represents a floor level in a building."""
    level: int
    name: str
    rooms: List[Room] = field(default_factory=list)
    height: float = 8.0  # Floor-to-ceiling height
    elevation: float = 0.0  # Elevation from ground level
    exterior_walls: List[Wall] = field(default_factory=list)
    interior_walls: List[Wall] = field(default_factory=list)
    
    def total_area(self) -> float:
        """Calculate total floor area."""
        return sum(room.area for room in self.rooms)


@dataclass
class RoofProfile:
    """Represents a roof profile from elevation."""
    points: List[Point]
    pitch: float = 0.0  # Roof pitch in degrees
    
    def __post_init__(self):
        """Calculate pitch if not provided."""
        if self.pitch == 0.0 and len(self.points) >= 2:
            self.pitch = self._calculate_pitch()
    
    def _calculate_pitch(self) -> float:
        """Calculate roof pitch from points."""
        if len(self.points) < 2:
            return 0.0
        
        # Find the steepest segment
        max_pitch = 0.0
        for i in range(len(self.points) - 1):
            dx = abs(self.points[i + 1].x - self.points[i].x)
            dz = abs(self.points[i + 1].z - self.points[i].z)
            if dx > 0:
                pitch = np.degrees(np.arctan(dz / dx))
                max_pitch = max(max_pitch, pitch)
        
        return max_pitch


@dataclass
class Elevation:
    """Represents an elevation view (front, rear, left, right)."""
    view: str  # 'front', 'rear', 'left', 'right'
    roof_profile: Optional[RoofProfile] = None
    windows: List[Window] = field(default_factory=list)
    doors: List[Door] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0
    foundation_height: float = 0.0


@dataclass
class Roof:
    """Represents a roof structure."""
    roof_type: str = "gable"  # gable, hip, flat, shed
    pitch: float = 30.0  # degrees
    overhang: float = 1.0  # feet
    profiles: List[RoofProfile] = field(default_factory=list)


@dataclass
class Building:
    """Represents a complete building with all floors and elevations."""
    floors: List[Floor] = field(default_factory=list)
    elevations: List[Elevation] = field(default_factory=list)
    roof: Optional[Roof] = None
    scale_factor: float = 1.0  # PDF units to real units
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))
    
    def total_height(self) -> float:
        """Calculate total building height."""
        if not self.floors:
            return 0.0
        
        max_elevation = max(
            floor.elevation + floor.height for floor in self.floors
        )
        
        # Add roof height if available
        if self.roof and self.roof.profiles:
            max_roof_height = max(
                max(p.z for p in profile.points) 
                for profile in self.roof.profiles
                if profile.points
            )
            max_elevation += max_roof_height
        
        return max_elevation
    
    def get_floor_by_level(self, level: int) -> Optional[Floor]:
        """Get floor by level number."""
        for floor in self.floors:
            if floor.level == level:
                return floor
        return None
    
    def get_elevation_by_view(self, view: str) -> Optional[Elevation]:
        """Get elevation by view name."""
        for elevation in self.elevations:
            if elevation.view.lower() == view.lower():
                return elevation
        return None
