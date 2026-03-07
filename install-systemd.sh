#!/usr/bin/env bash
# Flow2API Host Agent - systemd installer
# Usage: bash install-systemd.sh [install-dir]
set -euo pipefail

INSTALL_DIR="${1:-/opt/flow2api-host-agent}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3)"

if [ -z "$PYTHON" ]; then
  echo "python3 not found" >&2
  exit 1
fi

echo "==> Installing to: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy files

echo "==> Copying files..."
cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/web" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/systemd" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/docs" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
[ -f "$SCRIPT_DIR/agent.toml" ] && cp "$SCRIPT_DIR/agent.toml" "$INSTALL_DIR/" || cp "$SCRIPT_DIR/agent.example.toml" "$INSTALL_DIR/agent.toml"

# Install Python dependencies into project-local venv

echo "==> Creating virtual environment..."
"$PYTHON" -m venv "$INSTALL_DIR/.venv"
VENV_PYTHON="$INSTALL_DIR/.venv/bin/python"
VENV_UVICORN="$INSTALL_DIR/.venv/bin/uvicorn"

echo "==> Installing Python dependencies..."
"$VENV_PYTHON" -m pip install -U pip setuptools wheel >/dev/null
"$VENV_PYTHON" -m pip install -q -r "$INSTALL_DIR/requirements.txt"

# Ensure runtime directories
mkdir -p /var/log/flow2api-host-agent
mkdir -p /var/lib/flow2api-host-agent

# Write browser launcher service
cat > /etc/systemd/system/flow2api-host-agent-browser.service << EOF
[Unit]
Description=Flow2API Host Agent - Chrome Browser Launcher
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=$INSTALL_DIR
Environment=DISPLAY=:99
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$VENV_PYTHON $INSTALL_DIR/scripts/agent.py --config $INSTALL_DIR/agent.toml login
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
EOF

# Write daemon service
cat > /etc/systemd/system/flow2api-host-agent.service << EOF
[Unit]
Description=Flow2API Host Agent - Token Auto Refresh Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=DISPLAY=:99
ExecStart=$VENV_PYTHON $INSTALL_DIR/scripts/agent.py --config $INSTALL_DIR/agent.toml daemon
Restart=always
RestartSec=15
StandardOutput=append:/var/log/flow2api-host-agent/daemon.log
StandardError=append:/var/log/flow2api-host-agent/daemon.log

[Install]
WantedBy=multi-user.target
EOF

# Write Web UI service
cat > /etc/systemd/system/flow2api-host-agent-ui.service << EOF
[Unit]
Description=Flow2API Host Agent - Web UI
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$VENV_UVICORN web.app:app --host 0.0.0.0 --port 38110 --app-dir $INSTALL_DIR
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Optional daily restart timer
if [ -f "$INSTALL_DIR/systemd/flow2api-host-agent-daily-restart.service" ]; then
  cp "$INSTALL_DIR/systemd/flow2api-host-agent-daily-restart.service" /etc/systemd/system/
fi
if [ -f "$INSTALL_DIR/systemd/flow2api-host-agent-daily-restart.timer" ]; then
  cp "$INSTALL_DIR/systemd/flow2api-host-agent-daily-restart.timer" /etc/systemd/system/
fi

# Reload and enable

echo "==> Enabling services..."
systemctl daemon-reload
systemctl enable flow2api-host-agent-browser.service
systemctl enable flow2api-host-agent.service
systemctl enable flow2api-host-agent-ui.service

echo ""
echo "✅ Installation complete!"
echo ""
echo "Services installed:"
echo "  flow2api-host-agent-browser  - browser launcher (oneshot)"
echo "  flow2api-host-agent          - token auto-refresh daemon"
echo "  flow2api-host-agent-ui       - Web UI on port 38110"
[ -f "$INSTALL_DIR/systemd/flow2api-host-agent-daily-restart.timer" ] && echo "  flow2api-host-agent-daily-restart.timer - optional daily maintenance restart"
echo ""
echo "Important:"
echo "  - Connection Token must be the token string from Flow2API plugin settings, not a URL"
echo "  - novnc_url must use your SERVER IP/domain, not localhost, if accessed from another device"
echo ""
echo "Next steps:"
echo "  1. Edit config: $INSTALL_DIR/agent.toml"
echo "  2. Start browser and login: systemctl start flow2api-host-agent-browser"
echo "  3. Start Web UI: systemctl start flow2api-host-agent-ui"
echo "  4. Start daemon: systemctl start flow2api-host-agent"
[ -f "$INSTALL_DIR/systemd/flow2api-host-agent-daily-restart.timer" ] && echo "  5. (Optional) Enable daily restart: systemctl enable --now flow2api-host-agent-daily-restart.timer"
echo ""
echo "Health check: curl http://127.0.0.1:38110/api/health"
echo "Logs: journalctl -u flow2api-host-agent -f"
