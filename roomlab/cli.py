import argparse, json, webbrowser
from . import __version__
from .furniture import builtins
from .models import Project,Room
from .storage import Storage

def main(argv=None):
 p=argparse.ArgumentParser(prog='roomlab'); sub=p.add_subparsers(dest='command');
 s=sub.add_parser('serve'); s.add_argument('--host',default='127.0.0.1'); s.add_argument('--port',type=int,default=8787); s.add_argument('--reload',action='store_true')
 sub.add_parser('furniture'); sub.add_parser('projects'); sub.add_parser('version'); o=sub.add_parser('open'); o.add_argument('--port',type=int,default=8787)
 project=sub.add_parser('project'); ps=project.add_subparsers(dest='action');
 for action in ('create','delete'): q=ps.add_parser(action); q.add_argument('name')
 ps.add_parser('list')
 a=p.parse_args(argv); store=Storage()
 if a.command in (None,'serve'):
  import uvicorn; host=getattr(a,'host','127.0.0.1'); port=getattr(a,'port',8787); print(f'ROOMLAB\nServer running:\nhttp://{host}:{port}'); uvicorn.run('roomlab.server:app',host=host,port=port,reload=getattr(a,'reload',False))
 elif a.command=='version': print(__version__)
 elif a.command=='furniture':
  for x in builtins(): print(f'{x.name:28} {x.width:g} × {x.depth:g} in')
 elif a.command=='projects' or (a.command=='project' and a.action=='list'):
  for x in store.list(): print(x['name'])
 elif a.command=='project' and a.action=='create': store.save(Project(name=a.name,room=Room(width=108,length=144))); print(f'Created {a.name}')
 elif a.command=='project' and a.action=='delete': store.delete(a.name); print(f'Deleted {a.name}')
 elif a.command=='open': webbrowser.open(f'http://127.0.0.1:{a.port}')
if __name__=='__main__': main()
