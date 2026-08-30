"""Semantic, deterministic layout candidate generation and scoring."""
from copy import deepcopy
from itertools import product
from .geometry import (footprint, inside_room, collision_count, door_blockages,
    door_swing_blockages, wall_distances, usable_wall_segments, touches_wall,
    feature_overlap_on_wall, window_obstructions, intersects)
from .pathways import analyze_paths

WALLS=("north","south","west","east")

def semantic(item):
    """Supply useful behavior for old projects whose objects predate metadata."""
    name=item.name.lower()
    role=getattr(item,"furniture_role","other")
    if role != "other": return {"kind":role,"placement":item.placement_type,"anchor":item.anchor_edge}
    if getattr(item,"anchor_edge","none")=="head": return {"kind":"bed","placement":item.placement_type,"anchor":"head"}
    if getattr(item,"relationship",None)=="beside bed": return {"kind":"nightstand","placement":item.placement_type,"anchor":item.anchor_edge}
    if "bed" in name: return {"kind":"bed","placement":"wall_required","anchor":"head"}
    if "nightstand" in name: return {"kind":"nightstand","placement":"wall_preferred","anchor":"back"}
    if "dresser" in name or "chest" in name: return {"kind":"dresser","placement":"wall_required","anchor":"back"}
    return {"kind":"other","placement":getattr(item,"placement_type","freestanding"),"anchor":getattr(item,"anchor_edge","none")}

def _position_on_wall(item,wall,along,room):
    item.rotation=0 if wall in ("north","south") else 90; w,d=footprint(item)
    if wall=="north": item.x=along;item.y=0
    elif wall=="south": item.x=along;item.y=room.length-d
    elif wall=="west": item.x=0;item.y=along
    else: item.x=room.width-w;item.y=along
    return item

def bed_candidates(bed,room,features):
    """Meaningful centered, offset, and segment-boundary candidates on every wall."""
    result=[]
    for wall in WALLS:
        probe=deepcopy(bed);probe.rotation=0 if wall in ("north","south") else 90
        width=footprint(probe)[0] if wall in ("north","south") else footprint(probe)[1]
        for start,end in usable_wall_segments(wall,room,features,width):
            center=(start+end-width)/2
            positions=(start,end-width,center,center-12,center+12)
            for along in positions:
                candidate=_position_on_wall(deepcopy(bed),wall,max(start,min(end-width,along)),room)
                if not inside_room(candidate,room.width,room.length): continue
                if any(f.type in ("door","opening") and f.wall==wall and feature_overlap_on_wall(candidate,f) for f in features): continue
                key=(wall,round(candidate.x,2),round(candidate.y,2),candidate.rotation)
                if not any(x[0]==key for x in result): result.append((key,candidate,wall,abs(along-center)<.1))
    return [(item,wall,centered) for _,item,wall,centered in result]

def nightstand_options(nightstands,bed,wall,room):
    """Return both, left-only, right-only, and neither without leaving bounds."""
    if not nightstands:return [([],"none")]
    bw,bd=footprint(bed); candidates=[]
    for idx,n in enumerate(nightstands[:2]):
        n=deepcopy(n); nw,nd=footprint(n)
        if wall in ("north","south"):
            n.x=bed.x-nw if idx==0 else bed.x+bw;n.y=bed.y
        else:
            n.x=bed.x;n.y=bed.y-nd if idx==0 else bed.y+bd
        candidates.append(n if inside_room(n,room.width,room.length) else None)
    valid=[x for x in candidates if x]
    options=[]
    if len(valid)==2:options.append((valid,"both"))
    for i,x in enumerate(candidates):
        if x:options.append(([x],"left" if i==0 else "right"))
    options.append(([],"none"))
    return options

def dresser_candidates(dresser,room,features):
    result=[]
    for wall in WALLS:
        probe=deepcopy(dresser);probe.rotation=0 if wall in ("north","south") else 90
        along_size=footprint(probe)[0] if wall in ("north","south") else footprint(probe)[1]
        for start,end in usable_wall_segments(wall,room,features,along_size):
            for along in ((start+end-along_size)/2,start,end-along_size):
                d=_position_on_wall(deepcopy(dresser),wall,along,room)
                if inside_room(d,room.width,room.length):result.append((d,wall))
    return result

def _front_zone(item,wall,depth=30):
    from types import SimpleNamespace
    w,d=footprint(item)
    if wall=="north":return SimpleNamespace(x=item.x,y=item.y+d,width=w,depth=depth,rotation=0)
    if wall=="south":return SimpleNamespace(x=item.x,y=item.y-depth,width=w,depth=depth,rotation=0)
    if wall=="west":return SimpleNamespace(x=item.x+w,y=item.y,width=depth,depth=d,rotation=0)
    return SimpleNamespace(x=item.x-depth,y=item.y,width=depth,depth=d,rotation=0)

def score_layout(items,room,features,context=None):
    context=context or {}; outside=sum(not inside_room(x,room.width,room.length) for x in items)
    collisions=collision_count(items); openings=door_blockages(items,features,room); swings=door_swing_blockages(items,features,room)
    windows=window_obstructions(items,features,room); paths=analyze_paths(room,items,features)
    bed=next((x for x in items if semantic(x)["kind"]=="bed"),None); nights=[x for x in items if semantic(x)["kind"]=="nightstand"]
    dresser=next((x for x in items if semantic(x)["kind"]=="dresser"),None)
    bed_wall=context.get("bed_wall"); dresser_wall=context.get("dresser_wall")
    bed_contact=bool(bed and bed_wall and touches_wall(bed,bed_wall,room)); centered=context.get("bed_centered",False)
    access_clear=True
    if dresser and dresser_wall:
        zone=_front_zone(dresser,dresser_wall);access_clear=not any(intersects(zone,x) for x in items if x.id!=dresser.id)
    walkway=paths["minimum_walkway"] if paths["minimum_walkway"] is not None else 36
    breakdown={
      "bounds":max(0,10-outside*10),"collision":max(0,20-collisions*10),
      "door_clearance":max(0,15-openings*15-swings*7),"entry_path":15 if paths["entry_path"]=="Clear" else 8 if paths["entry_path"]=="Restricted" else 0,
      "walking_clearance":10 if walkway>=36 else 8 if walkway>=30 else 5 if walkway>=24 else 1,
      "bed_placement":10 if bed_contact else 0,"nightstand_relationship":8 if len(nights)>=2 else 5 if len(nights)==1 else 1,
      "dresser_placement":7 if dresser and dresser_wall and access_clear else 3 if dresser and dresser_wall else 0,
      "window_obstruction":max(0,3-windows*2),"symmetry":2 if centered and len(nights)==2 else 0}
    total=sum(breakdown.values())
    reasons=[]
    reasons.append(("✓" if paths["entry_path"]=="Clear" else "△" if paths["path_exists"] else "✕")+f" {paths['entry_path']} entrance")
    if bed_contact:reasons.append("✓ Bed headboard touches a usable wall")
    if centered:reasons.append("✓ Bed centered on wall")
    reasons.append(("✓" if len(nights)==2 else "△")+f" {len(nights)} nightstand{'s' if len(nights)!=1 else ''} fit beside bed")
    reasons.append(("✓" if walkway>=30 else "△")+f" Approx. {walkway:g}” primary walkway")
    if dresser:reasons.append(("✓" if access_clear else "△")+" Dresser access area "+("clear" if access_clear else "restricted"))
    if windows:reasons.append("△ Window preference obstruction")
    return max(0,min(100,round(total))),breakdown,reasons,{**paths,"collisions":collisions,"door_blockages":openings,"door_swing_blockages":swings,"window_obstructions":windows}

def generate(room,items,features):
    if not items:return []
    beds=[x for x in items if semantic(x)["kind"]=="bed"]
    if not beds:
        score,parts,reasons,analysis=score_layout(items,room,features)
        return [{"name":"Layout A","score":score,"score_breakdown":parts,"reasons":reasons,"analysis":analysis,"furniture":[x.model_dump() for x in items],"description":"Current semantic arrangement"}]
    bed=beds[0];nightstands=[x for x in items if semantic(x)["kind"]=="nightstand"]
    dressers=[x for x in items if semantic(x)["kind"]=="dresser"]
    fixed=[x for x in items if x.id not in {bed.id,*[n.id for n in nightstands],*[d.id for d in dressers]}]
    candidates=[]
    for placed_bed,bed_wall,centered in bed_candidates(bed,room,features):
      d_options=dresser_candidates(dressers[0],room,features) if dressers else [(None,None)]
      for (nights,nmode),(dresser,dwall) in product(nightstand_options(nightstands,placed_bed,bed_wall,room),d_options):
        arranged=[placed_bed,*nights,*fixed]+([dresser] if dresser else [])
        if sum(not inside_room(x,room.width,room.length) for x in arranged):continue
        if collision_count(arranged)>1:continue
        context={"bed_wall":bed_wall,"bed_centered":centered,"dresser_wall":dwall,"nightstand_mode":nmode}
        value,parts,reasons,analysis=score_layout(arranged,room,features,context)
        candidates.append({"score":value,"score_breakdown":parts,"reasons":reasons,"analysis":analysis,"furniture":[x.model_dump() for x in arranged],"description":f"Bed on {bed_wall} wall; {nmode} nightstands"})
    candidates.sort(key=lambda x:(x["score"],x["score_breakdown"]["walking_clearance"]),reverse=True)
    unique=[];seen=set()
    for x in candidates:
        signature=tuple((o["id"],round(o["x"],1),round(o["y"],1),o["rotation"]) for o in x["furniture"])
        if signature not in seen:seen.add(signature);unique.append(x)
        if len(unique)==3:break
    for i,x in enumerate(unique):x["name"]=f"Layout {chr(65+i)}"
    return unique

# Backwards-compatible public name.
def score(items,room,features):return score_layout(items,room,features)[0]
