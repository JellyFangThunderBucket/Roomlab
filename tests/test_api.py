from fastapi.testclient import TestClient
from roomlab.server import app

def test_assets_and_api(tmp_path,monkeypatch):
 c=TestClient(app)
 assert c.get('/').status_code==200
 assert c.get('/static/app.js').status_code==200
 assert len(c.get('/api/furniture').json())>=41
 assert c.get('/api/health').json()=={'status':'ok'}
