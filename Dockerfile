FROM python:3.12-slim

# System deps + Node.js for Claude Code CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Non-root user (Claude Code credentials mount to /home/sefer/.claude)
RUN useradd -m -s /bin/bash sefer
USER sefer

WORKDIR /app

# Python deps (install as root, then switch back)
USER root
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
RUN chown -R sefer:sefer /app
USER sefer

EXPOSE 2552

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "2552"]
