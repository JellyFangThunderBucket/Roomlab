from roomlab.models import PlacedItem
from roomlab.geometry import intersects,inside_room,wall_distances,rectangle_distance

def item(id,x,y,w=20,d=10): return PlacedItem(id=id,name=id,x=x,y=y,width=w,depth=d)
def test_geometry():
 a,b=item('a',0,0),item('b',15,5)
 assert intersects(a,b); assert not inside_room(b,30,12); assert wall_distances(a,100,100)=={'left':0,'right':80,'top':0,'bottom':90}
 assert rectangle_distance(a,item('c',30,0))==10
