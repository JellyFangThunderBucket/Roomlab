import json
from importlib.resources import files
from .models import FurnitureItem

def builtins(): return [FurnitureItem(**x) for x in json.loads(files("roomlab").joinpath("data/furniture.json").read_text())]

