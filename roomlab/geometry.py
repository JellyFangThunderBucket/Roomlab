from math import hypot

def footprint(item):
    return (item.depth, item.width) if item.rotation % 180 else (item.width, item.depth)

def rect(item):
    w, d = footprint(item); return item.x, item.y, item.x+w, item.y+d

def intersects(a, b, padding=0):
    ax1,ay1,ax2,ay2=rect(a); bx1,by1,bx2,by2=rect(b)
    return ax1 < bx2+padding and ax2+padding > bx1 and ay1 < by2+padding and ay2+padding > by1

def inside_room(item, width, length):
    x1,y1,x2,y2=rect(item); return x1 >= 0 and y1 >= 0 and x2 <= width and y2 <= length

def wall_distances(item, width, length):
    x1,y1,x2,y2=rect(item); return {"left":x1,"right":width-x2,"top":y1,"bottom":length-y2}

def rectangle_distance(a,b):
    ax1,ay1,ax2,ay2=rect(a); bx1,by1,bx2,by2=rect(b)
    return hypot(max(bx1-ax2,ax1-bx2,0), max(by1-ay2,ay1-by2,0))

def collision_count(items): return sum(intersects(a,b) for i,a in enumerate(items) for b in items[i+1:])

def door_rect(feature, room):
    from types import SimpleNamespace
    p,w=feature.position,feature.width
    if feature.wall in ("north","south"):
        return SimpleNamespace(x=p,y=0 if feature.wall=="north" else room.length-w,width=w,depth=w,rotation=0)
    return SimpleNamespace(x=0 if feature.wall=="west" else room.width-w,y=p,width=w,depth=w,rotation=0)

def wall_length(wall, room):
    return room.width if wall in ("north", "south") else room.length

def usable_wall_segments(wall, room, features, minimum=0):
    """Return wall intervals left after doors, openings and wall closets."""
    blocked=[]
    for f in features:
        if f.wall != wall or f.type not in ("door", "opening", "closet"): continue
        blocked.append((max(0, f.position), min(wall_length(wall, room), f.position+f.width)))
    merged=[]
    for start,end in sorted(blocked):
        if merged and start <= merged[-1][1]: merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else: merged.append((start,end))
    cursor=0; result=[]
    for start,end in merged:
        if start-cursor >= minimum and start > cursor: result.append((cursor,start))
        cursor=max(cursor,end)
    length=wall_length(wall,room)
    if length-cursor >= minimum: result.append((cursor,length))
    return result

def wall_interval(item, wall):
    x1,y1,x2,y2=rect(item)
    return (x1,x2) if wall in ("north","south") else (y1,y2)

def feature_overlap_on_wall(item, feature):
    a,b=wall_interval(item,feature.wall); return max(a,feature.position) < min(b,feature.position+feature.width)

def touches_wall(item, wall, room, tolerance=.01):
    d=wall_distances(item,room.width,room.length)
    return d[{"north":"top","south":"bottom","west":"left","east":"right"}[wall]] <= tolerance

def door_opening_intersects(item, feature, room, depth=3):
    """Furniture covering the physical opening strip."""
    from types import SimpleNamespace
    p,w=feature.position,feature.width
    if feature.wall=="north": opening=SimpleNamespace(x=p,y=0,width=w,depth=depth,rotation=0)
    elif feature.wall=="south": opening=SimpleNamespace(x=p,y=room.length-depth,width=w,depth=depth,rotation=0)
    elif feature.wall=="west": opening=SimpleNamespace(x=0,y=p,width=depth,depth=w,rotation=0)
    else: opening=SimpleNamespace(x=room.width-depth,y=p,width=depth,depth=w,rotation=0)
    return intersects(item,opening)

def door_hinge(feature, room):
    far=feature.position+feature.width if feature.hinge=="right" else feature.position
    if feature.wall=="north": return far,0
    if feature.wall=="south": return far,room.length
    if feature.wall=="west": return 0,far
    return room.width,far

def door_swing_intersects(item, feature, room):
    """Conservative quarter-circle swept-area test honoring wall, hinge and swing."""
    if feature.type != "door" or feature.swing == "out": return False
    hx,hy=door_hinge(feature,room); x1,y1,x2,y2=rect(item)
    cx=max(x1,min(hx,x2)); cy=max(y1,min(hy,y2))
    if hypot(cx-hx,cy-hy) > feature.width: return False
    # The interior half-plane plus the hinge-side quadrant defines the sweep.
    if feature.wall=="north": inward=y2>0; lateral=(x2>=hx if feature.hinge=="left" else x1<=hx)
    elif feature.wall=="south": inward=y1<room.length; lateral=(x2>=hx if feature.hinge=="left" else x1<=hx)
    elif feature.wall=="west": inward=x2>0; lateral=(y2>=hy if feature.hinge=="left" else y1<=hy)
    else: inward=x1<room.width; lateral=(y2>=hy if feature.hinge=="right" else y1<=hy)
    return inward and lateral

def door_blockages(items, features, room):
    return sum(door_opening_intersects(i,f,room) for f in features if f.type=="door" for i in items)

def door_swing_blockages(items, features, room):
    return sum(door_swing_intersects(i,f,room) for f in features if f.type=="door" for i in items)

def window_obstructions(items, features, room):
    total=0
    for f in features:
        if f.type != "window": continue
        for item in items:
            if touches_wall(item,f.wall,room) and feature_overlap_on_wall(item,f):
                total += 2 if item.blocks_window or not item.allow_under_window else 1
    return total

def access_zone(item, room, depth=None):
    """Return the inward service zone in front of wall-oriented furniture."""
    from types import SimpleNamespace
    x1,y1,x2,y2=rect(item); w,d=footprint(item)
    depth=float(depth if depth is not None else getattr(item,"preferred_clearance_front",30) or 30)
    distances=wall_distances(item,room.width,room.length); wall=min(distances,key=distances.get)
    if wall=="top": return SimpleNamespace(x=x1,y=y2,width=w,depth=depth,rotation=0,owner=item.id,kind="furniture")
    if wall=="bottom": return SimpleNamespace(x=x1,y=y1-depth,width=w,depth=depth,rotation=0,owner=item.id,kind="furniture")
    if wall=="left": return SimpleNamespace(x=x2,y=y1,width=depth,depth=d,rotation=0,owner=item.id,kind="furniture")
    return SimpleNamespace(x=x1-depth,y=y1,width=depth,depth=d,rotation=0,owner=item.id,kind="furniture")

def closet_access_zone(feature, room):
    """Planning-only clearance extending inward from a closet/opening."""
    from types import SimpleNamespace
    p,w=feature.position,feature.width; depth=getattr(feature,"access_clearance",36) or 36
    if feature.wall=="north": return SimpleNamespace(x=p,y=0,width=w,depth=depth,rotation=0,owner=feature.id,kind="closet")
    if feature.wall=="south": return SimpleNamespace(x=p,y=room.length-depth,width=w,depth=depth,rotation=0,owner=feature.id,kind="closet")
    if feature.wall=="west": return SimpleNamespace(x=0,y=p,width=depth,depth=w,rotation=0,owner=feature.id,kind="closet")
    return SimpleNamespace(x=room.width-depth,y=p,width=depth,depth=w,rotation=0,owner=feature.id,kind="closet")

def bed_access_zones(item, depth=24):
    """Side approach envelopes; the headboard edge is deliberately excluded."""
    from types import SimpleNamespace
    x1,y1,x2,y2=rect(item);w,d=footprint(item)
    if item.rotation%180:
        return [SimpleNamespace(x=x1,y=y1-depth,width=w,depth=depth,rotation=0,owner=item.id,kind="bed"),
                SimpleNamespace(x=x1,y=y2,width=w,depth=depth,rotation=0,owner=item.id,kind="bed")]
    return [SimpleNamespace(x=x1-depth,y=y1,width=depth,depth=d,rotation=0,owner=item.id,kind="bed"),
            SimpleNamespace(x=x2,y=y1,width=depth,depth=d,rotation=0,owner=item.id,kind="bed")]

def access_conflicts(items, features, room):
    """Report service-zone restrictions separately from physical collisions."""
    result={"closet":0,"desk":0,"dresser":0,"storage":0,"bed":0}
    for feature in features:
        if feature.type in ("closet","opening"):
            zone=closet_access_zone(feature,room)
            result["closet"] += sum(intersects(item,zone) for item in items)
    for item in items:
        name=item.name.lower(); role=getattr(item,"furniture_role","other")
        kind="desk" if role=="desk" or "desk" in name else "dresser" if role=="dresser" or "dresser" in name or "chest" in name else "storage" if role=="storage" or any(x in name for x in ("cabinet","wardrobe","bookshelf")) else None
        if kind:
            zone=access_zone(item,room,36 if kind=="desk" else 30)
            result[kind] += sum(intersects(other,zone) for other in items if other.id!=item.id)
        if getattr(item,"furniture_role","other")=="bed" or " bed" in f" {name}":
            result["bed"] += sum(any(intersects(other,zone) for other in items if other.id!=item.id) for zone in bed_access_zones(item))
    return result
