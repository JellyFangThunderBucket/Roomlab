from roomlab.models import Room,PlacedItem
from roomlab.layout import generate
from roomlab.geometry import inside_room

def test_three_layouts():
 room=Room(width=108,length=144); items=[PlacedItem(id='b',name='King Bed',category='Beds',width=76,depth=80),PlacedItem(id='n1',name='Standard Nightstand',width=24,depth=18),PlacedItem(id='n2',name='Standard Nightstand',width=24,depth=18),PlacedItem(id='d',name='Standard Dresser',width=60,depth=20)]
 layouts=generate(room,items,[])
 assert len(layouts)==3 and layouts[0]['score']>=layouts[-1]['score']
 assert all(0<=x['score']<=100 for x in layouts)
