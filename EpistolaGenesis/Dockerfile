FROM python:3.12-slim

# System dependencies for Odoo 15
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libjpeg-dev \
    libffi-dev \
    zlib1g-dev \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    poppler-utils \
    node-less \
    npm \
    git \
    curl \
    && npm install -g rtlcss \
    && rm -rf /var/lib/apt/lists/*

# wkhtmltopdf (not in Debian Trixie repos, install from GitHub release)
RUN curl -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb -o /tmp/wkhtmltox.deb \
    && apt-get update && apt-get install -y --no-install-recommends /tmp/wkhtmltox.deb \
    && rm /tmp/wkhtmltox.deb && rm -rf /var/lib/apt/lists/*

WORKDIR /odoo

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir "setuptools<81" wheel \
    && pip install --no-cache-dir -r requirements.txt 2>/dev/null || \
    pip install --no-cache-dir -r requirements.txt --ignore-installed 2>/dev/null || true \
    && pip install --no-cache-dir pandas numpy phonenumbers

# Odoo source
COPY odoo/ odoo/
COPY odoo-bin .

# Addons
COPY modulos/ modulos/

# Config
COPY conf/odoo-docker.conf /etc/odoo/odoo.conf

# Data directory
RUN mkdir -p /var/lib/odoo && chmod 755 /var/lib/odoo

EXPOSE 8069 8072

CMD ["python", "odoo-bin", "-c", "/etc/odoo/odoo.conf"]
