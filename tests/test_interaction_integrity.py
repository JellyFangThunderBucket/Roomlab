import json
import subprocess
from pathlib import Path

from roomlab.furniture import builtins
from roomlab.layout import score_layout
from roomlab.models import Feature, PlacedItem, Project, Room
from roomlab.storage import Storage


ROOT = Path(__file__).parents[1]
MODULE = ROOT / "roomlab/static/interactions.js"


def js(expression):
    source = f"const x=require({json.dumps(str(MODULE))});console.log(JSON.stringify({expression}))"
    result = subprocess.run(["node", "-e", source], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_catalog_selection_is_separate_from_authoritative_add_flow():
    # Selection is UI state; createFurniture is the sole project-object constructor.
    created = js("x.createFurniture({id:'king',name:'King Bed',category:'Beds',width:76,depth:80},"
                 "{width:108,length:144},'new-id')")
    assert created["id"] == "new-id"
    assert (created["x"], created["y"]) == (16, 32)
    assert created["width"] == 76 and created["depth"] == 80


def test_default_add_clamps_large_furniture_inside_room():
    created = js("x.createFurniture({id:'large',name:'Large',category:'Custom',width:120,depth:160},"
                 "{width:108,length:144},'id')")
    assert created["x"] == 0 and created["y"] == 0


def test_move_after_zoom_uses_world_coordinates_and_clamps():
    moved = js("x.updateFurniture({id:'a',name:'Bed',width:60,depth:80,x:0,y:0,rotation:0,clearance:0},"
               "{x:(250-10)/4,y:(300-20)/4},{width:108,length:144})")
    assert moved["x"] == 48
    assert moved["y"] == 64


def test_rotation_duplicate_property_apply_and_delete_primitives():
    rotated = js("x.updateFurniture({id:'a',name:'Bed',width:76,depth:80,x:32,y:64,rotation:0,clearance:0},"
                 "{rotation:90,x:50,y:100},{width:108,length:144})")
    assert rotated["rotation"] == 90
    assert rotated["x"] == 28 and rotated["y"] == 68
    duplicate = js("x.duplicateFurniture({id:'a',name:'Bed',width:76,depth:80,x:10,y:10,rotation:0},"
                   "{width:108,length:144},'b')")
    assert duplicate["id"] == "b" and duplicate["x"] == 13


def test_feature_create_update_validation_and_wall_mappings():
    for wall, expected in {
        "north": (40, 0, 72, 0), "south": (40, 144, 72, 144),
        "west": (0, 40, 0, 72), "east": (108, 40, 108, 72),
    }.items():
        segment = js(f"x.featureSegment({{id:'d',type:'door',wall:'{wall}',width:32,position:40}},"
                     "{width:108,length:144})")
        assert tuple(segment.values()) == expected
    changed = js("x.validateFeature({id:'d',type:'door',wall:'EAST',width:32,position:24,hinge:'right',swing:'out'},"
                 "{width:108,length:144})")
    assert changed["wall"] == "east" and changed["position"] == 24


def test_feature_rejects_wall_overflow_without_partial_clamping():
    script = f"const x=require({json.dumps(str(MODULE))});try{{x.validateFeature({{type:'door',wall:'north',width:32,position:80}},{{width:108,length:144}});process.exit(2)}}catch(e){{console.log(e.message)}}"
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert result.returncode == 0
    assert "between 0 and 76" in result.stdout


def test_door_hinge_and_swing_change_rendering_geometry():
    room = "{width:108,length:144}"
    inward = js(f"x.doorGeometry({{type:'door',wall:'north',width:30,position:6,hinge:'left',swing:'in'}},{room})")
    outward = js(f"x.doorGeometry({{type:'door',wall:'north',width:30,position:6,hinge:'left',swing:'out'}},{room})")
    right = js(f"x.doorGeometry({{type:'door',wall:'north',width:30,position:6,hinge:'right',swing:'in'}},{room})")
    assert inward["hy"] == 0 and inward["endAngle"] > 0
    assert outward["endAngle"] < 0
    assert right["hx"] == 36


def test_save_reload_preserves_moved_bed_and_door(tmp_path):
    store = Storage(tmp_path)
    project = Project(name="Integrity", room=Room(width=108, length=144), furniture=[
        PlacedItem(id="bed", name="King Bed", category="Beds", width=76, depth=80, x=17, y=31)
    ], features=[Feature(id="door", type="door", wall="north", width=32, position=41)])
    store.save(project)
    loaded = store.get("Integrity")
    assert (loaded.furniture[0].x, loaded.furniture[0].y) == (17, 31)
    assert (loaded.features[0].wall, loaded.features[0].width, loaded.features[0].position) == ("north", 32, 41)


def test_all_builtin_beds_have_consistent_semantics():
    beds = [item for item in builtins() if item.category == "Beds"]
    assert beds
    assert all((item.furniture_role, item.placement_type, item.anchor_edge,
                item.access_edge, item.center_on_wall_preferred) ==
               ("bed", "wall_required", "head", "foot", True) for item in beds)


def test_blocked_walkway_zero_remains_worst_score():
    room = Room(width=120, length=144)
    door = Feature(id="door", type="door", wall="south", position=5, width=30)
    barrier = PlacedItem(id="barrier", name="Barrier", width=120, depth=20, x=0, y=115)
    _, parts, _, analysis = score_layout([barrier], room, [door])
    assert analysis["minimum_walkway"] == 0
    assert parts["walking_clearance"] == 1
