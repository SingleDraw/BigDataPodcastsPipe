FROM python:3.11-slim

# Install only minimal required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libglib2.0-0 libnss3 libx11-6 libxcomposite1 libxdamage1 \
      libxext6 libxrandr2 libxcb1 libxkbcommon0 libasound2 \
      libatk1.0-0 libatk-bridge2.0-0 libxfixes3 libgbm1 libexpat1 \
      libnspr4 libdbus-1-3 libatspi2.0-0 libcairo2 && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man /usr/share/locale


# Set working directory
WORKDIR /app

# Copy only necessary files
COPY ./app ./app
COPY ./setup.py ./setup.py

# Add entrypoint
RUN cat <<"EOF" > /app/entrypoint && \
chmod +x /app/entrypoint && \
sed -i 's/\r$//' /app/entrypoint
#!/bin/bash
if [ -z "$1" ]; then
  exec test --help
fi

case "$1" in
  test)
    echo "Starting scraping..."
    exec test "${@:2}"
    ;;
  *)
    echo "Unknown command: $1"
    echo "Usage: test [args]"
    exit 1
    ;;
esac
EOF

# Install Python deps
RUN pip install --no-cache-dir .

ENTRYPOINT ["/app/entrypoint"]
CMD ["test"]
