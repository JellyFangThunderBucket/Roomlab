import pytest
from roomlab.models import Room, PlacedItem, Feature
from roomlab.geometry import (usable_wall_segments, door_opening_intersects,
    door_swing_intersects, window_obstructions)
from roomlab.layout import bed_candidates, nightstand_options, dresser_candidates, generate, score_layout
from roomlab.pathways import analyze_paths


def piece(id,name,w,d,**kw):
    return PlacedItem(id=id,name=name,width=w,depth=d,**kw)


def bedroom(width=108,length=144):
    room=Room(width=width,length=length)
    items=[piece('bed','King Bed',76,80,category='Beds',placement_type='wall_required',anchor_edge='head'),
      piece('n1','Standard Nightstand',24,18),piece('n2','Standard Nightstand',24,18),
      piece('dresser','Standard Dresser',60,20,placement_type='wall_required',anchor_edge='back',access_edge='front')]
    return room,items


def test_usable_wall_segments_subtract_openings_not_windows():
    room=Room(width=144,length=120)
    features=[Feature(id='d',type='door',wall='north',position=0,width=30),Feature(id='w',type='window',wall='north',position=60,width=36)]
    assert usable_wall_segments('north',room,features)==[(30,144)]
    assert usable_wall_segments('north',room,features,100)==[(30,144)]


def test_many_bed_candidates_and_no_headboard_over_door():
    room,items=bedroom(); door=Feature(id='d',type='door',wall='south',position=4,width=30)
    candidates=bed_candidates(items[0],room,[door])
    assert len(candidates)>=10
    assert {wall for _,wall,_ in candidates}=={'north','east','west'}
    assert all(not (wall=='south' and bed.x<34 and bed.x+bed.width>4) for bed,wall,_ in candidates)


def test_nightstands_are_optional_and_never_outside():
    room,items=bedroom(); bed=[x for x,w,c in bed_candidates(items[0],room,[]) if w=='north'][0]
    options=nightstand_options(items[1:3],bed,'north',room)
    modes={mode for _,mode in options}
    assert 'none' in modes and ('left' in modes or 'right' in modes)
    assert all(0<=x.x and x.x+x.width<=room.width for group,_ in options for x in group)


def test_dresser_candidates_touch_usable_walls():
    room,items=bedroom(); candidates=dresser_candidates(items[3],room,[])
    assert len(candidates)>=8
    assert {wall for _,wall in candidates}=={'north','south','east','west'}


def test_door_opening_and_sweep_are_distinct():
    room=Room(width=108,length=144); door=Feature(id='d',type='door',wall='south',position=4,width=30,hinge='left',swing='in')
    covering=piece('a','Chair',10,10,x=8,y=136)
    swept=piece('b','Chair',8,8,x=7,y=116)
    assert door_opening_intersects(covering,door,room)
    assert door_swing_intersects(swept,door,room)
    door.swing='out'; assert not door_swing_intersects(swept,door,room)


def test_window_semantics_penalize_blocker_more_than_bed():
    room=Room(width=120,length=144); window=Feature(id='w',type='window',wall='north',position=20,width=50)
    bed=piece('b','Bed',60,80,x=20,y=0,allow_under_window=True)
    wardrobe=piece('w','Wardrobe',48,24,x=20,y=0,allow_under_window=False,blocks_window=True)
    assert window_obstructions([bed],[window],room)==1
    assert window_obstructions([wardrobe],[window],room)==2


def test_entry_path_clear_and_blocked_and_walkway():
    room=Room(width=120,length=144); door=Feature(id='d',type='door',wall='south',position=5,width=30)
    clear=analyze_paths(room,[],[door]); assert clear['path_exists'] and clear['minimum_walkway']>=30
    barrier=piece('x','Barrier',120,20,x=0,y=115)
    blocked=analyze_paths(room,[barrier],[door]); assert not blocked['path_exists'] and blocked['entry_path']=='Blocked'


def test_regression_rooms_generate_explainable_candidates():
    for width,length in ((108,144),(119,152)):
        room,items=bedroom(width,length); door=Feature(id='d',type='door',wall='south',position=4,width=30)
        layouts=generate(room,items,[door])
        assert len(layouts)==3
        assert all(x['score_breakdown'] and x['reasons'] and 'entry_path' in x['analysis'] for x in layouts)
        assert layouts==sorted(layouts,key=lambda x:x['score'],reverse=True)


def test_physical_fit_is_distinct_from_poor_usability():
    room=Room(width=80,length=100); bed=piece('b','King Bed',76,80,x=2,y=0)
    assert bed.width<=room.width and bed.depth<=room.length
    score,parts,reasons,analysis=score_layout([bed],room,[])
    assert parts['walking_clearance']<10
