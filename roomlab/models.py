from typing import Literal
from pydantic import BaseModel, Field

class FurnitureItem(BaseModel):
    id: str; name: str; category: str; width: float = Field(gt=0); depth: float = Field(gt=0)
    height: float | None = None; label: str = ""; rotation_allowed: bool = True
    default_clearance: float = 24; notes: str = ""
    placement_type: Literal["wall_required", "wall_preferred", "freestanding"] = "freestanding"
    anchor_edge: Literal["head", "back", "none"] = "none"
    preferred_clearance_front: float = 24
    preferred_clearance_back: float = 0
    preferred_clearance_left: float = 12
    preferred_clearance_right: float = 12
    access_edge: Literal["front", "foot", "multiple", "none"] = "none"
    allow_under_window: bool = True
    blocks_window: bool = False
    center_on_wall_preferred: bool = False
    relationship: str | None = None
    furniture_role: Literal["bed", "nightstand", "dresser", "other"] = "other"

class PlacedItem(BaseModel):
    id: str; catalog_id: str = "custom-rectangle"; name: str; category: str = "Custom"
    x: float = 0; y: float = 0; width: float = Field(gt=0); depth: float = Field(gt=0)
    rotation: int = 0; clearance: float = 0
    placement_type: Literal["wall_required", "wall_preferred", "freestanding"] = "freestanding"
    anchor_edge: Literal["head", "back", "none"] = "none"
    preferred_clearance_front: float = 24
    preferred_clearance_back: float = 0
    preferred_clearance_left: float = 12
    preferred_clearance_right: float = 12
    access_edge: Literal["front", "foot", "multiple", "none"] = "none"
    allow_under_window: bool = True
    blocks_window: bool = False
    center_on_wall_preferred: bool = False
    relationship: str | None = None
    furniture_role: Literal["bed", "nightstand", "dresser", "other"] = "other"

class Feature(BaseModel):
    id: str; type: Literal["door", "window", "closet", "opening", "radiator", "fireplace", "column"]
    wall: Literal["north", "south", "east", "west"] = "north"; position: float = 12
    width: float = 30; depth: float = 4; hinge: str = "left"; swing: str = "in"

class Room(BaseModel):
    width: float = Field(gt=0, le=2400); length: float = Field(gt=0, le=2400)

class Project(BaseModel):
    name: str; room: Room
    furniture: list[PlacedItem] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)
    settings: dict = Field(default_factory=lambda: {"units":"feet", "grid":3, "snap":True, "show_clearances":False})

class LayoutRequest(BaseModel):
    room: Room; furniture: list[PlacedItem]
    features: list[Feature] = Field(default_factory=list)
