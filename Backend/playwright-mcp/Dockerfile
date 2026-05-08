FROM node:22-slim

# Install system deps for Chromium headless
RUN apt-get update && apt-get install -y \
    wget curl ca-certificates \
    libnss3 libatk-bridge2.0-0 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxfixes3 libxi6 libxrandr2 libgbm1 libxss1 \
    libpango-1.0-0 libpangocairo-1.0-0 libasound2 libatspi2.0-0 \
    libgtk-3-0 fonts-liberation \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Docker mode: virtual display + VNC + noVNC so the browser window is viewable
RUN apt-get update && apt-get install -y \
    xvfb x11vnc novnc \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install @playwright/mcp globally (this brings its own playwright dep)
RUN npm install -g @playwright/mcp@latest

# Install the exact chromium revision that the bundled playwright inside @playwright/mcp needs.
# The playwright CLI lives at: $(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js
# We direct it to install browsers into /ms-playwright via PLAYWRIGHT_BROWSERS_PATH.
RUN PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    node "$(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js" \
    install chromium --with-deps

COPY Backend/playwright-mcp/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8931
# noVNC web viewer
EXPOSE 6080

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Starts Xvfb + VNC + noVNC + Playwright MCP (headed)
CMD ["/start.sh"]
