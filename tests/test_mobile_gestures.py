import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
GESTURES = ROOT / "roomlab/static/gestures.js"
INDEX = (ROOT / "roomlab/static/index.html").read_text()
STYLES = (ROOT / "roomlab/static/styles.css").read_text()
APP = (ROOT / "roomlab/static/app.js").read_text()


def run_node(expression):
    script = f"const g=require({json.dumps(str(GESTURES))});console.log(JSON.stringify({expression}))"
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_pinch_scales_and_honors_zoom_limits():
    camera = "{scale:2,ox:10,oy:20,minScale:.5,maxScale:5}"
    zoomed = run_node(f"g.pinchCamera({camera},{{x:50,y:50}},{{x:150,y:50}},{{x:0,y:50}},{{x:200,y:50}})")
    assert zoomed["scale"] == 4
    maximum = run_node(f"g.pinchCamera({camera},{{x:99,y:50}},{{x:101,y:50}},{{x:0,y:50}},{{x:1000,y:50}})")
    assert maximum["scale"] == 5
    minimum = run_node(f"g.pinchCamera({camera},{{x:0,y:50}},{{x:1000,y:50}},{{x:49,y:50}},{{x:51,y:50}})")
    assert minimum["scale"] == .5


def test_pinch_keeps_world_point_under_moving_midpoint():
    camera = {"scale": 2, "ox": 10, "oy": 20}
    result = run_node(
        "g.pinchCamera({scale:2,ox:10,oy:20,minScale:.15,maxScale:15},"
        "{x:50,y:100},{x:150,y:100},{x:90,y:130},{x:290,y:130})"
    )
    old_world = ((100 - camera["ox"]) / camera["scale"], (100 - camera["oy"]) / camera["scale"])
    new_midpoint = (190, 130)
    new_world = ((new_midpoint[0] - result["ox"]) / result["scale"],
                 (new_midpoint[1] - result["oy"]) / result["scale"])
    assert new_world == old_world


def test_button_zoom_anchors_requested_screen_point():
    result = run_node("g.zoomAt({scale:2,ox:10,oy:20,minScale:.15,maxScale:15},{x:100,y:80},4)")
    assert (100 - result["ox"]) / result["scale"] == 45
    assert (80 - result["oy"]) / result["scale"] == 30


def test_mobile_shell_and_touch_handlers_are_present():
    for sheet in ("furniture", "features", "properties", "analysis"):
        assert f'data-sheet="{sheet}"' in INDEX
    assert 'id="zoomIn"' in INDEX and 'id="zoomOut"' in INDEX
    assert 'id="sheetBackdrop"' in INDEX
    assert "env(safe-area-inset-top)" in STYLES
    assert "env(safe-area-inset-bottom)" in STYLES
    assert "touch-action:none" in STYLES
    assert "activePointers" in APP
    assert "Gesture.pinchCamera" in APP
    assert "hitFurniture(p,e.pointerType)" in APP
    assert "window.addEventListener('resize'" in APP


def test_sheet_state_has_open_close_and_escape_paths():
    assert "function openSheet(name)" in APP
    assert "function closeSheets()" in APP
    assert "$('#sheetBackdrop').onclick=closeSheets" in APP
    assert "document.querySelector('.mobileSheet.open')" in APP


def test_mobile_catalog_action_is_anchored_outside_scrolling_catalog():
    scroll_start = INDEX.index('id="catalogScroll"')
    scroll_end = INDEX.index('</div><div id="catalogAction"', scroll_start)
    action_start = INDEX.index('id="catalogAction"')
    assert scroll_start < scroll_end < action_start
    assert "#catalogScroll{flex:1 1 auto" in STYLES
    assert "#catalogAction{position:relative" in STYLES
    assert "env(safe-area-inset-bottom)" in STYLES
    assert "ADD TO ROOM" in INDEX


def test_filter_clears_a_selected_item_that_is_no_longer_visible():
    assert "catalogSelected&&!matches.some" in APP
    assert "catalogSelected=null;showCatalogAction(null)" in APP
    assert 'aria-pressed="${catalogSelected===x.id}"' in APP


def test_add_failures_are_visible_and_do_not_close_the_sheet():
    handler = APP[APP.index("$('#addSelectedFurniture').onclick"):APP.index(";$('#search').oninput")]
    assert "try{addFurniture(c);closeSheets()}catch(err)" in handler
    assert "console.error('Could not add furniture',err)" in handler
    assert "setStatus(`Could not add furniture: ${err.message}`,true)" in handler


def test_mobile_status_is_a_transient_hidden_toast():
    assert "$('#status').hidden=isMobile()" in APP
    assert "if(isMobile()){el.hidden=true;el.textContent=''}else el.textContent='Ready'" in APP
    assert "#status[hidden]{display:none!important}" in STYLES
    assert "#status{top:calc(var(--header-h) + 8px);bottom:auto}" in STYLES
