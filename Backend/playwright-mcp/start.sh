#!/bin/sh
# Docker mode: start virtual display, VNC, noVNC, then Playwright MCP (headed)

# 1920x1200: wide enough for 1920 viewport + extra height for Chromium's address bar (~88px)
Xvfb :99 -screen 0 1920x1200x24 &
export DISPLAY=:99
sleep 1

# VNC server captures :99 and listens on port 5900 (no password)
x11vnc -display :99 -forever -shared -rfbport 5900 -nopw -quiet &
sleep 1

# Minimal viewer: no noVNC toolbar/controls, view-only, scales to fill any container
cat > /usr/share/novnc/viewer.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 100%; height: 100%; overflow: hidden; background: #000; }
  #screen { width: 100%; height: 100%; }
</style>
</head>
<body>
<div id="screen"></div>
<script type="module">
import RFB from '/core/rfb.js';
const rfb = new RFB(
  document.getElementById('screen'),
  `ws://${location.hostname}:${location.port}/websockify`
);
const params = new URLSearchParams(location.search);
rfb.viewOnly = params.get('interactive') !== '1'; // view-only by default; ?interactive=1 enables input
rfb.scaleViewport = true;  // canvas always fills the div — resizes with iframe
rfb.resizeSession = false;
rfb.addEventListener('disconnect', () => setTimeout(() => location.reload(), 2000));
</script>
</body>
</html>
HTMLEOF

# noVNC web client + WebSocket proxy on port 6080
websockify --web=/usr/share/novnc/ 6080 localhost:5900 &
sleep 1

# Playwright MCP — headed (no --headless), uses DISPLAY=:99
# viewport matches Xvfb width; height leaves room for Chromium's UI chrome (~88px)
exec npx @playwright/mcp \
  --host 0.0.0.0 --port 8931 \
  --browser chromium \
  --allowed-hosts "*" \
  --shared-browser-context \
  --image-responses allow \
  --viewport-size "1920,1080"
