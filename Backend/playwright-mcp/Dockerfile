FROM node:22-slim

# Install system deps for Chromium headless
RUN apt-get update && apt-get install -y \
    wget curl ca-certificates \
    libnss3 libatk-bridge2.0-0 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxfixes3 libxi6 libxrandr2 libgbm1 libxss1 \
    libpango-1.0-0 libpangocairo-1.0-0 libasound2 libatspi2.0-0 \
    libgtk-3-0 fonts-liberation \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install @playwright/mcp globally (this brings its own playwright dep)
RUN npm install -g @playwright/mcp@latest

# Install the exact chromium revision that the bundled playwright inside @playwright/mcp needs.
# The playwright CLI lives at: $(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js
# We direct it to install browsers into /ms-playwright via PLAYWRIGHT_BROWSERS_PATH.
RUN PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    node "$(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js" \
    install chromium --with-deps

EXPOSE 8931

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

CMD ["npx", "@playwright/mcp", "--host", "0.0.0.0", "--port", "8931", \
     "--headless", "--browser", "chromium", "--allowed-hosts", "*", \
     "--shared-browser-context", "--image-responses", "allow"]
