from roomlab.models import LayoutRequest, Room
from roomlab.server import analyze, furniture, health, index, static


def test_assets_and_api(tmp_path, monkeypatch):
    response = index()
    assert response.status_code == 200
    assert str(response.path).endswith("index.html")
    assert (static / "app.js").is_file()
    assert (static / "gestures.js").is_file()
    assert (static / "interactions.js").is_file()
    assert len(furniture()) >= 41
    assert health() == {"status": "ok"}


def test_analysis_endpoint():
    payload = LayoutRequest(room=Room(width=108, length=144), furniture=[], features=[])
    response = analyze(payload)
    assert "score_breakdown" in response
