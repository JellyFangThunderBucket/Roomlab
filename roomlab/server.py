from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import Project, FurnitureItem, LayoutRequest
from .furniture import builtins
from .layout import generate
from .storage import Storage

static=Path(__file__).parent/'static'; app=FastAPI(title='ROOMLAB',version='1.0.0'); store=Storage()
app.mount('/static',StaticFiles(directory=static),name='static')
@app.get('/')
def index(): return FileResponse(static/'index.html')
@app.get('/api/health')
def health(): return {'status':'ok'}
@app.get('/api/furniture')
def furniture(): return [x.model_dump() for x in builtins()]+store.custom()
@app.post('/api/furniture/custom')
def custom(item:FurnitureItem): return store.add_custom(item)
@app.get('/api/projects')
def projects(): return store.list()
@app.get('/api/projects/{name}')
def project(name:str):
    try:return store.get(name)
    except (ValueError,FileNotFoundError) as e: raise HTTPException(404,str(e))
@app.put('/api/projects/{name}')
def save(name:str,p:Project):
    if name!=p.name: raise HTTPException(400,'URL and project names must match')
    try:return store.save(p)
    except ValueError as e: raise HTTPException(422,str(e))
@app.delete('/api/projects/{name}',status_code=204)
def delete(name:str):
    try:store.delete(name)
    except (ValueError,FileNotFoundError) as e: raise HTTPException(404,str(e))
@app.post('/api/projects/{name}/duplicate/{new_name}')
def duplicate(name:str,new_name:str):
    try:return store.duplicate(name,new_name)
    except (ValueError,FileNotFoundError) as e: raise HTTPException(422,str(e))
@app.post('/api/layout')
def layout(req:LayoutRequest): return generate(req.room,req.furniture,req.features)
@app.post('/api/export')
def export(p:Project): return p
