import json
import time

from roomlab.geometry import access_conflicts, access_zone, closet_access_zone, intersects
from roomlab.layout import circulation_rating, generate, score_layout
from roomlab.models import Feature, PlacedItem, Project, Room


def item(id, name, width, depth, role="other", placement="freestanding", **kw):
    return PlacedItem(id=id, name=name, width=width, depth=depth,
                      furniture_role=role, placement_type=placement, **kw)


def working_bedroom():
    room = Room(width=119, length=152)
    furniture = [
        item("bed", "Full Bed", 54, 75, "bed", "wall_required", anchor_edge="head"),
        item("night", "Small Nightstand", 18, 16, "nightstand", "wall_preferred"),
        item("dresser", "Small Dresser", 48, 18, "dresser", "wall_required", anchor_edge="back"),
        item("desk", "Desk", 48, 24, "desk", "wall_preferred", anchor_edge="back",
             preferred_clearance_front=36),
    ]
    features = [
        Feature(id="door", type="door", wall="south", position=5, width=30),
        Feature(id="closet", type="closet", wall="north", position=90, width=24,
                depth=24, access_clearance=36),
    ]
    return room, furniture, features


def test_smart_arrange_returns_three_distinct_explainable_layouts_quickly():
    room, furniture, features = working_bedroom()
    started = time.monotonic(); layouts = generate(room, furniture, features)
    assert time.monotonic() - started < 3
    assert len(layouts) == 3
    assert len({layout["variant_key"] for layout in layouts}) == 3
    for layout in layouts:
        assert 0 <= layout["score"] <= 100
        assert set(("physical_validity", "circulation", "feature_access",
                    "furniture_usability", "composition")) <= set(layout["score_breakdown"])
        assert layout["reasons"] and layout["analysis"]["physical_fit"]
        assert layout["analysis"]["collisions"] == 0


def test_best_layout_keeps_north_east_closet_access_clear():
    room, furniture, features = working_bedroom()
    best = generate(room, furniture, features)[0]
    assert best["analysis"]["closet_access_conflicts"] == 0
    zone = closet_access_zone(features[1], room)
    assert not any(intersects(PlacedItem(**placed), zone) for placed in best["furniture"])


def test_desk_chair_zone_obstruction_reduces_usability_score():
    room = Room(width=120, length=144)
    desk = item("desk", "Desk", 48, 24, "desk", "wall_preferred", x=36, y=0,
                anchor_edge="back", preferred_clearance_front=36)
    blocker = item("chair", "Large blocker", 48, 24, x=36, y=28)
    clear_score = score_layout([desk], room, [], {"desk_wall": "north"})
    blocked_score = score_layout([desk, blocker], room, [], {"desk_wall": "north"})
    assert access_conflicts([desk, blocker], [], room)["desk"] == 1
    assert blocked_score[1]["furniture_usability"] < clear_score[1]["furniture_usability"]
    assert blocked_score[3]["desk_access_conflicts"] == 1


def test_physical_fit_and_circulation_rating_remain_distinct():
    room = Room(width=80, length=100)
    bed = item("bed", "King Bed", 76, 80, "bed", "wall_required", x=2, y=0)
    _, _, _, analysis = score_layout([bed], room, [])
    assert analysis["physical_fit"] is True
    assert analysis["circulation_rating"] in ("POOR", "TIGHT")
    assert circulation_rating(0, False) == "BLOCKED"


def test_door_swing_conflict_is_reported_and_penalized():
    room = Room(width=108, length=144)
    door = Feature(id="door", type="door", wall="south", position=4, width=30,
                   hinge="left", swing="in")
    chair = item("chair", "Chair", 8, 8, x=7, y=116)
    _, breakdown, reasons, analysis = score_layout([chair], room, [door])
    assert analysis["door_swing_blockages"] == 1
    assert breakdown["feature_access"] < 20
    assert any("Door swing conflict" in reason for reason in reasons)


def test_old_project_json_defaults_variants_and_feature_access():
    old = json.dumps({"name":"Old","room":{"width":108,"length":144},
                      "furniture":[],"features":[{"id":"c","type":"closet",
                      "wall":"north","position":12,"width":30}],"settings":{}})
    project = Project.model_validate_json(old)
    assert project.layout_variants == []
    assert project.features[0].access_clearance == 36


def test_project_layout_variants_round_trip():
    project = Project(name="Variants", room=Room(width=108, length=144),
                      layout_variants=[{"name":"Layout A","score":92,
                                        "furniture":[{"id":"bed","x":12,"y":0}]}])
    loaded = Project.model_validate_json(project.model_dump_json())
    assert loaded.layout_variants[0]["name"] == "Layout A"
    assert loaded.layout_variants[0]["furniture"][0]["x"] == 12
