#!/bin/bash
# Fix WSL2 Docker connectivity issues

echo "🔧 Fixing WSL2 Docker connectivity..."

# 1. Update DNS settings
echo "📡 Updating DNS..."
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 2. Restart Docker
echo "🔄 Restarting Docker..."
sudo systemctl restart docker || sudo service docker restart

# 3. Test connectivity
echo "🧪 Testing Docker Hub connectivity..."
timeout 10 docker pull hello-world:latest && echo "✅ Docker Hub is accessible!" || echo "❌ Still having issues"

echo ""
echo "💡 If this didn't work, try these Windows commands (run in PowerShell as Admin):"
echo "   wsl --shutdown"
echo "   Then restart WSL and try again"
