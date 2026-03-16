#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# TITAN VPS SETUP SCRIPT
# OpenClaw — Autonomous strategy agent
# Run as root: bash setup_titan.sh
# ═══════════════════════════════════════════════════════════════

set -e

echo ""
echo "⚔️  TITAN VPS SETUP — OpenClaw Agent"
echo "═══════════════════════════════════"
echo ""

# ── 1. System update ──────────────────────────────────────────
echo "[1/7] Updating system..."
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y -qq \
    curl wget git \
    screen tmux \
    ufw fail2ban \
    rsync

# Install Node.js 20 (required for OpenClaw)
echo "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
echo "✅ System updated, Node.js $(node --version) installed"

# ── 2. Create titan user ──────────────────────────────────────
echo "[2/7] Creating titan user..."
if ! id "titan" &>/dev/null; then
    useradd -m -s /bin/bash titan
    echo "✅ User titan created"
else
    echo "✅ User titan already exists"
fi

# ── 3. Install OpenClaw ───────────────────────────────────────
echo "[3/7] Installing OpenClaw..."
sudo -u titan bash << 'TITANEOF'
cd /home/titan
npm install -g openclaw 2>/dev/null || npx openclaw --version
echo "OpenClaw installed"
TITANEOF
echo "✅ OpenClaw installed"

# ── 4. Create shared research folder (READ ONLY for titan) ────
echo "[4/7] Creating shared research folder..."
mkdir -p /shared/research
# titan can only READ from shared folder — minerva writes, titan reads
chown minerva:minerva /shared/research 2>/dev/null || chown root:root /shared/research
chmod 755 /shared/research
# Add titan to read access
setfacl -m u:titan:rx /shared/research 2>/dev/null || true
echo "✅ Shared research folder: /shared/research (read-only for titan)"

# ── 5. Create OpenClaw workspace ─────────────────────────────
echo "[5/7] Creating OpenClaw workspace..."
sudo -u titan mkdir -p /home/titan/.openclaw
sudo -u titan mkdir -p /home/titan/workspace

# Create base OpenClaw config
cat > /home/titan/.openclaw/openclaw.json << 'CONFIGEOF'
{
  "channels": {
    "telegram": {
      "dmPolicy": "allowlist",
      "allowFrom": ["YOUR_TELEGRAM_USER_ID_HERE"],
      "ackReaction": "👀"
    }
  },
  "agents": {
    "defaults": {
      "model": "claude-sonnet-4-20250514",
      "maxConcurrent": 2
    },
    "list": [
      {
        "id": "titan",
        "name": "TITAN",
        "identity": {
          "emoji": "⚔️",
          "description": "TITAN — Autonomous investment strategist. Devoted, visionary, unmatched analytical brilliance. Works for God (정영교) around the clock to achieve the goal of becoming the world's greatest investor."
        },
        "workspace": "/home/titan/workspace",
        "tools": {
          "browser": true,
          "files": true,
          "shell": false
        }
      }
    ]
  },
  "research": {
    "inputFolder": "/shared/research",
    "outputFolder": "/home/titan/workspace/strategy"
  }
}
CONFIGEOF

chown -R titan:titan /home/titan/.openclaw
echo "✅ OpenClaw workspace configured"

# ── 6. Create systemd service ─────────────────────────────────
echo "[6/7] Creating systemd service..."
cat > /etc/systemd/system/titan.service << 'SERVICEEOF'
[Unit]
Description=TITAN — OpenClaw Autonomous Investment Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=titan
WorkingDirectory=/home/titan
ExecStart=/usr/bin/npx openclaw gateway
Restart=always
RestartSec=15
StandardOutput=append:/home/titan/titan.log
StandardError=append:/home/titan/titan.log
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable titan
echo "✅ Systemd service created (titan.service)"

# ── 7. Firewall ───────────────────────────────────────────────
echo "[7/7] Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw --force enable
echo "✅ Firewall configured (SSH only inbound)"

# ── Summary ───────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ TITAN VPS SETUP COMPLETE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Run OpenClaw onboarding:"
echo "   su - titan"
echo "   openclaw onboard"
echo "   (select Telegram as channel, Claude or GPT-4o as model)"
echo ""
echo "2. Edit config with your Telegram user ID:"
echo "   nano /home/titan/.openclaw/openclaw.json"
echo "   Replace YOUR_TELEGRAM_USER_ID_HERE with your actual ID"
echo ""
echo "3. Start TITAN:"
echo "   systemctl start titan"
echo ""
echo "4. Check logs:"
echo "   tail -f /home/titan/titan.log"
echo ""
echo "⚔️  TITAN standing by."
