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

def door_blockages(items, features, room):
    return sum(intersects(i,door_rect(f,room)) for f in features if f.type=="door" for i in items)

