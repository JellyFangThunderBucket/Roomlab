"""Small grid-based circulation analysis; all public measurements are inches."""
from collections import deque
from .geometry import rect

def _occupied(room, items, grid):
    cols=max(1,int(room.width//grid)); rows=max(1,int(room.length//grid)); blocked=set()
    for item in items:
        x1,y1,x2,y2=rect(item)
        for y in range(max(0,int(y1//grid)),min(rows,int((y2-1e-6)//grid)+1)):
            for x in range(max(0,int(x1//grid)),min(cols,int((x2-1e-6)//grid)+1)): blocked.add((x,y))
    return cols,rows,blocked

def _door_starts(door, room, grid, cols, rows):
    cells=[]
    a=int(door.position//grid); b=int((door.position+door.width)//grid)
    if door.wall in ("north","south"):
        y=0 if door.wall=="north" else rows-1; cells=[(x,y) for x in range(a,min(cols,b+1))]
    else:
        x=0 if door.wall=="west" else cols-1; cells=[(x,y) for y in range(a,min(rows,b+1))]
    return cells

def analyze_paths(room, items, features, grid=3):
    """BFS from primary door to central open area, with approximate path width."""
    cols,rows,blocked=_occupied(room,items,grid); doors=[f for f in features if f.type=="door"]
    if not doors:
        if not items: walkway=36
        else:
            gaps=[]
            for item in items:
                x1,y1,x2,y2=rect(item)
                gaps.extend(v for v in (x1,room.width-x2,y1,room.length-y2) if v>0)
            walkway=min(36,max(gaps,default=0))
        return {"entry_path":"No door", "path_exists":True, "minimum_walkway":walkway}
    starts=[c for c in _door_starts(doors[0],room,grid,cols,rows) if c not in blocked]
    if not starts: return {"entry_path":"Blocked", "path_exists":False, "minimum_walkway":0}
    targets={(x,y) for x in range(cols//3,max(cols//3+1,2*cols//3+1)) for y in range(rows//3,max(rows//3+1,2*rows//3+1)) if (x,y) not in blocked}
    q=deque(starts); previous={c:None for c in starts}; end=None
    while q:
        c=q.popleft()
        if c in targets: end=c; break
        for n in ((c[0]+1,c[1]),(c[0]-1,c[1]),(c[0],c[1]+1),(c[0],c[1]-1)):
            if 0<=n[0]<cols and 0<=n[1]<rows and n not in blocked and n not in previous: previous[n]=c;q.append(n)
    if end is None: return {"entry_path":"Blocked", "path_exists":False, "minimum_walkway":0}
    path=[]
    while end is not None: path.append(end);end=previous[end]
    def width(cell):
        # Distance to furniture approximates transverse corridor width. Room edges
        # are deliberately excluded: a path beginning on a doorway is not 3” wide.
        if not blocked:return 36
        distance=min(abs(cell[0]-x)+abs(cell[1]-y) for x,y in blocked)
        return min(36,max(grid,(distance*2-1)*grid))
    interior=path[:-2] if len(path)>3 else path
    walkway=min(width(c) for c in interior); status="Clear" if walkway>=30 else "Restricted"
    return {"entry_path":status,"path_exists":True,"minimum_walkway":walkway}
