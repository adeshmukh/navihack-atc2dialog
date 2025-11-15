# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir --root-user-action=ignore uv

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install Python dependencies using uv
# Install everything declared in pyproject.toml to stay in sync automatically
RUN uv pip install --system .

# Copy application code
COPY . .

# Expose Chainlit port
EXPOSE 8000

# TLS configuration (build args)
ARG ENABLE_TLS=false
ARG TLS_CERT=/certs/chainlit-dev.crt
ARG TLS_KEY=/certs/chainlit-dev.key

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHAINLIT_HOST=0.0.0.0
ENV CHAINLIT_PORT=8000
ENV PIP_ROOT_USER_ACTION=ignore
ENV ENABLE_TLS=${ENABLE_TLS}
ENV TLS_CERT=${TLS_CERT}
ENV TLS_KEY=${TLS_KEY}

# Run Chainlit application with conditional TLS support
CMD ["sh", "-c", "if [ \"$ENABLE_TLS\" = \"true\" ] && [ -f \"$TLS_CERT\" ] && [ -f \"$TLS_KEY\" ]; then chainlit run app.py --host 0.0.0.0 --port 8000 --ssl-certfile $TLS_CERT --ssl-keyfile $TLS_KEY; else chainlit run app.py --host 0.0.0.0 --port 8000; fi"]

