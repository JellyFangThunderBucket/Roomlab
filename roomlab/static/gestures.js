(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.RoomlabGestures = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const MIN_SCALE = 0.15;
  const MAX_SCALE = 15;

  function clampScale(value, minimum = MIN_SCALE, maximum = MAX_SCALE) {
    return Math.max(minimum, Math.min(maximum, value));
  }

  function midpoint(a, b) {
    return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  }

  function distance(a, b) {
    return Math.hypot(b.x - a.x, b.y - a.y);
  }

  function zoomAt(camera, screenPoint, nextScale) {
    const scale = clampScale(nextScale, camera.minScale, camera.maxScale);
    const worldX = (screenPoint.x - camera.ox) / camera.scale;
    const worldY = (screenPoint.y - camera.oy) / camera.scale;
    return {
      scale,
      ox: screenPoint.x - worldX * scale,
      oy: screenPoint.y - worldY * scale,
    };
  }

  function pinchCamera(startCamera, startA, startB, currentA, currentB) {
    const startMid = midpoint(startA, startB);
    const currentMid = midpoint(currentA, currentB);
    const startDistance = Math.max(1, distance(startA, startB));
    const ratio = distance(currentA, currentB) / startDistance;
    const worldX = (startMid.x - startCamera.ox) / startCamera.scale;
    const worldY = (startMid.y - startCamera.oy) / startCamera.scale;
    const scale = clampScale(
      startCamera.scale * ratio,
      startCamera.minScale,
      startCamera.maxScale,
    );
    return {
      scale,
      ox: currentMid.x - worldX * scale,
      oy: currentMid.y - worldY * scale,
    };
  }

  return { MIN_SCALE, MAX_SCALE, clampScale, midpoint, distance, zoomAt, pinchCamera };
});
