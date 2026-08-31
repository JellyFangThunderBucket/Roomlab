"""Deterministic semantic candidate generation and explainable scoring."""
from copy import deepcopy
from itertools import product
from .geometry import (footprint, inside_room, collision_count, door_blockages,
    door_swing_blockages, wall_distances, usable_wall_segments, touches_wall,
    feature_overlap_on_wall, window_obstructions, intersects, access_conflicts,
    access_zone)
from .pathways import analyze_paths

WALLS=("north","south","west","east")

def semantic(item):
    """Use catalog metadata, with compatibility inference for old projects."""
    name=item.name.lower(); role=getattr(item,"furniture_role","other")
    if role != "other": return {"kind":role,"placement":item.placement_type,"anchor":item.anchor_edge}
    if getattr(item,"anchor_edge","none")=="head" or " bed" in f" {name}": return {"kind":"bed","placement":"wall_required","anchor":"head"}
    if getattr(item,"relationship",None)=="beside bed" or "nightstand" in name: return {"kind":"nightstand","placement":"wall_preferred","anchor":"back"}
    if "dresser" in name or "chest" in name: return {"kind":"dresser","placement":"wall_required","anchor":"back"}
    if "desk" in name: return {"kind":"desk","placement":"wall_preferred","anchor":"back"}
    if any(x in name for x in ("wardrobe","cabinet","bookshelf","buffet","console","tv stand")): return {"kind":"storage","placement":"wall_preferred","anchor":"back"}
    if any(x in name for x in ("sofa","loveseat","recliner")): return {"kind":"sofa","placement":"wall_preferred","anchor":"back"}
    if "dining" in name and "table" in name: return {"kind":"dining","placement":"freestanding","anchor":"none"}
    return {"kind":"other","placement":getattr(item,"placement_type","freestanding"),"anchor":getattr(item,"anchor_edge","none")}

def _position_on_wall(item,wall,along,room):
    item.rotation=0 if wall in ("north","south") else 90; w,d=footprint(item)
    if wall=="north": item.x=along;item.y=0
    elif wall=="south": item.x=along;item.y=room.length-d
    elif wall=="west": item.x=0;item.y=along
    else: item.x=room.width-w;item.y=along
    return item

def wall_candidates(item,room,features,offsets=(-12,0,12)):
    """Generate segment boundaries, centers and modest offsets without inch-grid brute force."""
    result=[];seen=set()
    for wall in WALLS:
        probe=deepcopy(item);probe.rotation=0 if wall in ("north","south") else 90
        size=footprint(probe)[0] if wall in ("north","south") else footprint(probe)[1]
        for start,end in usable_wall_segments(wall,room,features,size):
            center=(start+end-size)/2
            for along in (start,end-size,*(center+x for x in offsets)):
                placed=_position_on_wall(deepcopy(item),wall,max(start,min(end-size,along)),room)
                if not inside_room(placed,room.width,room.length):continue
                key=(wall,round(placed.x,1),round(placed.y,1),placed.rotation)
                if key not in seen:seen.add(key);result.append((placed,wall,abs(along-center)<.1))
    return result

def bed_candidates(bed,room,features):
    result=[]
    for candidate,wall,centered in wall_candidates(bed,room,features):
        if any(f.type in ("door","opening","closet") and f.wall==wall and feature_overlap_on_wall(candidate,f) for f in features):continue
        result.append((candidate,wall,centered))
    return result

def nightstand_options(nightstands,bed,wall,room):
    if not nightstands:return [([],"none")]
    bw,bd=footprint(bed); candidates=[]
    for idx,n in enumerate(nightstands[:2]):
        n=deepcopy(n);nw,nd=footprint(n)
        if wall in ("north","south"):n.x=bed.x-nw if idx==0 else bed.x+bw;n.y=bed.y
        else:n.x=bed.x;n.y=bed.y-nd if idx==0 else bed.y+bd
        candidates.append(n if inside_room(n,room.width,room.length) else None)
    options=[];valid=[x for x in candidates if x]
    if len(valid)==2:options.append((valid,"both"))
    for i,x in enumerate(candidates):
        if x:options.append(([x],"left" if i==0 else "right"))
    options.append(([],"none"));return options

def dresser_candidates(dresser,room,features):return [(x,w) for x,w,_ in wall_candidates(dresser,room,features,offsets=(0,))]
def desk_candidates(desk,room,features):return [(x,w) for x,w,_ in wall_candidates(desk,room,features,offsets=(-12,0,12))]

def circulation_rating(value,path_exists=True):
    if not path_exists or value<=0:return "BLOCKED"
    if value>=36:return "EXCELLENT"
    if value>=30:return "GOOD"
    if value>=24:return "TIGHT"
    return "POOR"

def score_layout(items,room,features,context=None):
    context=context or {};outside=sum(not inside_room(x,room.width,room.length) for x in items);collisions=collision_count(items)
    openings=door_blockages(items,features,room);swings=door_swing_blockages(items,features,room);windows=window_obstructions(items,features,room)
    paths=analyze_paths(room,items,features);walkway=paths["minimum_walkway"] if paths["minimum_walkway"] is not None else 0
    access=access_conflicts(items,features,room);closets=access["closet"]
    bed=next((x for x in items if semantic(x)["kind"]=="bed"),None);nights=[x for x in items if semantic(x)["kind"]=="nightstand"]
    desk=next((x for x in items if semantic(x)["kind"]=="desk"),None);dresser=next((x for x in items if semantic(x)["kind"]=="dresser"),None)
    bed_wall=context.get("bed_wall");desk_wall=context.get("desk_wall");dresser_wall=context.get("dresser_wall")
    bed_contact=bool(bed and bed_wall and touches_wall(bed,bed_wall,room));centered=context.get("bed_centered",False)
    physical=max(0,25-outside*25-collisions*15)
    circulation=(15 if paths["entry_path"]=="Clear" else 7 if paths["path_exists"] else 0)+(10 if walkway>=36 else 8 if walkway>=30 else 5 if walkway>=24 else 1 if walkway>0 else 0)
    feature_access=max(0,20-openings*15-swings*8-closets*8-windows*3)
    furniture_usability=0
    if bed:furniture_usability+=6 if bed_contact else 1;furniture_usability+=4 if len(nights)>=2 else 3 if len(nights)==1 else 0;furniture_usability+=2 if access["bed"]==0 else 1 if access["bed"]==1 else 0
    if dresser:furniture_usability+=5 if dresser_wall and not access["dresser"] else 2 if dresser_wall else 0
    if desk:furniture_usability+=5 if desk_wall and not access["desk"] else 2 if desk_wall else 0
    furniture_usability=min(20,furniture_usability+(5 if not bed and not dresser and not desk else 0))
    wall_oriented=sum(1 for x in items if semantic(x)["placement"]!="freestanding");wall_context=sum(bool(v) for v in (bed_wall,dresser_wall,desk_wall))
    composition=min(10,3+(3 if centered else 0)+min(4,wall_context)+(1 if wall_oriented and wall_context else 0))
    categories={"physical_validity":physical,"circulation":circulation,"feature_access":feature_access,"furniture_usability":furniture_usability,"composition":composition}
    total=max(0,min(100,round(sum(categories.values()))));rating=circulation_rating(walkway,paths["path_exists"])
    reasons=[("✓" if paths["entry_path"]=="Clear" else "△" if paths["path_exists"] else "✕")+f" {paths['entry_path']} entry path",f"{'✓' if walkway>=30 else '△'} {walkway:g}” approx. primary walkway"]
    if bed_contact:reasons.append("✓ Bed headboard on wall")
    if nights:reasons.append(f"✓ {len(nights)} nightstand{'s' if len(nights)!=1 else ''} beside bed")
    if desk:reasons.append(("✓" if not access["desk"] else "△")+" Desk chair/work zone "+("clear" if not access["desk"] else "restricted"))
    if dresser:reasons.append(("✓" if not access["dresser"] else "△")+" Dresser access "+("clear" if not access["dresser"] else "restricted"))
    if closets:reasons.append("△ Closet access restricted")
    if swings:reasons.append("✕ Door swing conflict")
    breakdown={**categories,"bounds":physical,"collision":physical,"door_clearance":feature_access,"entry_path":15 if paths["entry_path"]=="Clear" else 0,"walking_clearance":10 if walkway>=36 else 8 if walkway>=30 else 5 if walkway>=24 else 1,"bed_placement":6 if bed_contact else 0,"nightstand_relationship":4 if len(nights)>=2 else 3 if nights else 0,"dresser_placement":5 if dresser_wall and not access["dresser"] else 0,"window_obstruction":max(0,3-windows),"symmetry":3 if centered else 0}
    analysis={**paths,"circulation_rating":rating,"collisions":collisions,"door_blockages":openings,"door_swing_blockages":swings,"closet_access_conflicts":closets,"window_obstructions":windows,"bed_access_conflicts":access["bed"],"desk_access_conflicts":access["desk"],"dresser_access_conflicts":access["dresser"],"storage_access_conflicts":access["storage"],"physical_fit":outside==0}
    return total,breakdown,reasons,analysis

def _candidate_record(arranged,room,features,context,description):
    value,parts,reasons,analysis=score_layout(arranged,room,features,context)
    return {"score":value,"score_breakdown":parts,"reasons":reasons,"analysis":analysis,"furniture":[x.model_dump() for x in arranged],"description":description,"variant_key":context.get("bed_wall") or context.get("desk_wall") or "current"}

def generate(room,items,features):
    if not items:return []
    beds=[x for x in items if semantic(x)["kind"]=="bed"];nights=[x for x in items if semantic(x)["kind"]=="nightstand"]
    dressers=[x for x in items if semantic(x)["kind"]=="dresser"];desks=[x for x in items if semantic(x)["kind"]=="desk"]
    if not beds:
        major=desks[0] if desks else dressers[0] if dressers else None
        if not major:return [_candidate_record(items,room,features,{},"Current arrangement")]
        options=desk_candidates(major,room,features) if desks else dresser_candidates(major,room,features);fixed=[x for x in items if x.id!=major.id]
        candidates=[]
        for placed,wall in options:
            arranged=[placed,*fixed]
            if not collision_count(arranged):candidates.append(_candidate_record(arranged,room,features,{"desk_wall":wall} if desks else {"dresser_wall":wall},f"{major.name} on {wall} wall"))
    else:
        bed=beds[0];excluded={bed.id,*[x.id for x in nights],*[x.id for x in dressers],*[x.id for x in desks]};fixed=[x for x in items if x.id not in excluded];candidates=[]
        for placed_bed,bwall,centered in bed_candidates(bed,room,features):
            nopts=nightstand_options(nights,placed_bed,bwall,room)
            dopts=dresser_candidates(dressers[0],room,features)[:12] if dressers else [(None,None)]
            kopts=desk_candidates(desks[0],room,features)[:16] if desks else [(None,None)]
            accepted=0
            for (placed_nights,nmode),(dresser,dwall),(desk,kwall) in product(nopts,dopts,kopts):
                arranged=[placed_bed,*placed_nights,*fixed]+([dresser] if dresser else [])+([desk] if desk else [])
                if collision_count(arranged) or any(not inside_room(x,room.width,room.length) for x in arranged):continue
                context={"bed_wall":bwall,"bed_centered":centered,"dresser_wall":dwall,"desk_wall":kwall}
                candidates.append(_candidate_record(arranged,room,features,context,f"Bed on {bwall}; {nmode} nightstand; "+(f"desk on {kwall}" if desk else "open floor focus")))
                accepted += 1
                if accepted>=18:break
    candidates.sort(key=lambda x:(x["score"],x["score_breakdown"]["circulation"]),reverse=True)
    unique=[];signatures=set();walls=set()
    # First favor genuinely different major-wall arrangements.
    for candidate in candidates:
        signature=tuple(sorted((o["id"],round(o["x"]/6),round(o["y"]/6),o["rotation"]) for o in candidate["furniture"]))
        if signature in signatures:continue
        key=candidate["variant_key"]
        if key in walls and len(walls)<3:continue
        signatures.add(signature);walls.add(key);unique.append(candidate)
        if len(unique)==3:break
    if len(unique)<3:
        for candidate in candidates:
            signature=tuple(sorted((o["id"],round(o["x"]/6),round(o["y"]/6),o["rotation"]) for o in candidate["furniture"]))
            if signature not in signatures:signatures.add(signature);unique.append(candidate)
            if len(unique)==3:break
    for i,x in enumerate(unique):x["name"]=f"Layout {chr(65+i)}";x["badge"]="BEST OVERALL" if i==0 else "ALTERNATIVE"
    return unique

def score(items,room,features):return score_layout(items,room,features)[0]
