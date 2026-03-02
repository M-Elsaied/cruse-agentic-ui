#!/usr/bin/env bash
# EC2 bootstrap script for CRUSE production deployment.
# Run as root (or via user_data) on a fresh Ubuntu 24.04 instance.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/M-Elsaied/cruse-agentic-ui.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
INSTALL_DIR="/opt/cruse"

echo "==> Updating system packages..."
apt-get update -y
apt-get upgrade -y

echo "==> Installing Docker Engine..."
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker

echo "==> Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "    Directory exists, pulling latest..."
    cd "$INSTALL_DIR"
    git fetch origin
    git reset --hard "origin/$REPO_BRANCH"
else
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo "==> Setting up environment..."
ENV_FILE="$INSTALL_DIR/deploy/cruse/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$INSTALL_DIR/deploy/cruse/.env.example" "$ENV_FILE"
    echo "WARNING: .env created from example. Edit $ENV_FILE with real values before starting."
    echo "    Then run: cd $INSTALL_DIR/deploy/cruse && docker compose -f docker-compose.prod.yml up -d"
    exit 0
fi

echo "==> Starting services..."
cd "$INSTALL_DIR/deploy/cruse"
docker compose -f docker-compose.prod.yml up -d --build

echo "==> Done! Services starting. Check status with:"
echo "    cd $INSTALL_DIR/deploy/cruse && docker compose -f docker-compose.prod.yml ps"
