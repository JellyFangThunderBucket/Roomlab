from copy import deepcopy
from .geometry import footprint, inside_room, collision_count, door_blockages, wall_distances

def _place_wall(items, room, wall):
    result=deepcopy(items); bed=next((x for x in result if 'bed' in x.name.lower()), result[0] if result else None)
    if not bed: return result
    if wall in ('north','south'):
        bed.rotation=0; w,d=footprint(bed); bed.x=max(0,(room.width-w)/2); bed.y=0 if wall=='north' else room.length-d
    else:
        bed.rotation=90; w,d=footprint(bed); bed.x=0 if wall=='west' else room.width-w; bed.y=max(0,(room.length-d)/2)
    remaining=[x for x in result if x.id!=bed.id]; nights=[x for x in remaining if 'nightstand' in x.name.lower()]
    others=[x for x in remaining if x not in nights]
    bw,bd=footprint(bed)
    for idx,n in enumerate(nights[:2]):
        nw,nd=footprint(n)
        if wall in ('north','south'):
            n.x=bed.x-nw if idx==0 else bed.x+bw; n.y=bed.y
        else:
            n.x=bed.x; n.y=bed.y-nd if idx==0 else bed.y+bd
    for idx,o in enumerate(others):
        ow,od=footprint(o)
        if wall=='north': o.x=max(0,(room.width-ow)/2); o.y=room.length-od
        elif wall=='south': o.x=max(0,(room.width-ow)/2); o.y=0
        elif wall=='west': o.x=room.width-ow; o.y=max(0,(room.length-od)/2)
        else: o.x=0; o.y=max(0,(room.length-od)/2)
    return result

def score(items,room,features):
    outside=sum(not inside_room(x,room.width,room.length) for x in items); collisions=collision_count(items); doors=door_blockages(items,features,room)
    wall_bonus=sum(min(wall_distances(x,room.width,room.length).values()) < .01 for x in items)
    return max(0,min(100,96 + wall_bonus - outside*35-collisions*15-doors*25))

def generate(room,items,features):
    layouts=[]
    for wall in ('north','south','west','east'):
        placed=_place_wall(items,room,wall); layouts.append({'score':score(placed,room,features),'furniture':[x.model_dump() for x in placed],'description':f'Bed headboard on {wall} wall'})
    layouts.sort(key=lambda x:x['score'],reverse=True)
    for i,x in enumerate(layouts[:3]): x['name']=f"Layout {chr(65+i)}"
    return layouts[:3]
