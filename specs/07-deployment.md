# 07 - Deployment

> Status: **Draft** | Last updated: 2026-03-28

## Target

- **Host**: sachielNode (192.168.1.52)
- **User**: jota
- **Method**: Docker Compose + Cloudflare Tunnel
- **Domain**: yostesis.online (Namecheap)
- **URLs**:
  - `sefer.yostesis.online` -> Sefer (FastAPI)
  - `akua.yostesis.online` -> Odoo 15

## Docker Setup

```yaml
# See docker-compose.yml in repo root
services: db, odoo, sefer, nginx
```

## Environment Variables

| Variable              | Description                        | Required |
|-----------------------|------------------------------------|----------|
| ANTHROPIC_API_KEY     | Claude API key for Claude Code CLI | Yes      |
| POSTGRES_PASSWORD     | PostgreSQL password                | Yes      |
| SEFER_MODEL           | Claude model (default: sonnet)     | No       |

## Deploy Steps

### 1. Install Docker on sachielNode

```bash
ssh jota@192.168.1.52

# Install Docker (Arch/Manjaro)
sudo pacman -S docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker jota
# Log out and back in for group to take effect
```

If sachielNode is Debian/Ubuntu:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker jota
```

### 2. Clone and configure

```bash
cd /home/jota
git clone git@github.com:Jota-FalseProphet/sefer.git
cd sefer
cp .env.example .env
nano .env  # Set ANTHROPIC_API_KEY and POSTGRES_PASSWORD
```

### 3. Set up Cloudflare (one-time)

#### 3a. Move DNS to Cloudflare

1. Go to https://dash.cloudflare.com and create an account (free plan)
2. Click "Add a site" -> enter `yostesis.online`
3. Select the **Free** plan
4. Cloudflare will show you two nameservers (e.g., `ada.ns.cloudflare.com`, `bob.ns.cloudflare.com`)
5. Go to https://namecheap.com -> Domain List -> yostesis.online -> Nameservers
6. Change from "Namecheap BasicDNS" to **"Custom DNS"**
7. Enter the two Cloudflare nameservers
8. Save. Wait for propagation (usually 5-30 minutes, max 24h)
9. Back in Cloudflare, click "Check nameservers" to verify

#### 3b. Install cloudflared on sachielNode

```bash
# Debian/Ubuntu
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Arch/Manjaro
sudo pacman -S cloudflared
# or: yay -S cloudflared
```

#### 3c. Create and configure the tunnel

```bash
# Authenticate with Cloudflare
cloudflared tunnel login
# This opens a browser - select yostesis.online

# Create tunnel
cloudflared tunnel create sefer

# Note the tunnel UUID printed (e.g., a1b2c3d4-...)
# A credentials file is created at ~/.cloudflared/<UUID>.json
```

Create the tunnel config:
```bash
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <TUNNEL_UUID>
credentials-file: /home/jota/.cloudflared/<TUNNEL_UUID>.json

ingress:
  - hostname: sefer.yostesis.online
    service: http://localhost:80
  - hostname: akua.yostesis.online
    service: http://localhost:80
  - service: http_status:404
EOF
```

Create DNS records for the tunnel:
```bash
cloudflared tunnel route dns sefer sefer.yostesis.online
cloudflared tunnel route dns sefer akua.yostesis.online
```

#### 3d. Run the tunnel as a service

```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

### 4. Start services

```bash
cd /home/jota/sefer
docker compose up -d --build
```

### 5. Verify

```bash
# Check containers are running
docker compose ps

# Check health
curl http://localhost:2552/api/health
curl http://localhost:8069

# Check from outside (after tunnel is up)
curl https://sefer.yostesis.online/api/health
curl https://akua.yostesis.online
```

## Update Flow

```
local dev -> git push -> ssh sachielNode
  -> cd /home/jota/sefer
  -> git pull
  -> docker compose up -d --build
```

## Open Questions

- [ ] CI/CD pipeline or manual deploy?
- [ ] Log aggregation on sachielNode?
- [ ] Backup strategy for PostgreSQL data volume?
- [ ] SSL: Cloudflare handles HTTPS termination (Full mode recommended)
