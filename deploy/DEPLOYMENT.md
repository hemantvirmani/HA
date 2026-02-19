# Home Assistant Dashboard Deployment Guide

This guide explains how to deploy your Home Assistant dashboard using the Python script and how to reload YAML configurations via command line.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Deployment Script](#deployment-script)
3. [YAML Configuration Reload](#yaml-configuration-reload)
4. [SSH Setup](#ssh-setup)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Prerequisites

1. **SSH access** to your Home Assistant server
2. **Python 3.6+**

### Install Python Dependencies

#### Option A: Install Directly (Quick Start)

```bash
pip install -r deploy/requirements.txt
```

#### Option B: Use Virtual Environment (Recommended)

Using a virtual environment keeps your Python dependencies isolated:

**On Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r deploy/requirements.txt

# When done, deactivate
deactivate
```

**On Linux/Mac:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r deploy/requirements.txt

# When done, deactivate
deactivate
```

**Why use a virtual environment?**
- ✅ Keeps dependencies isolated from system Python
- ✅ Avoids version conflicts with other projects
- ✅ Easy to recreate or delete
- ✅ Best practice for Python projects

**Note:** After activating the virtual environment, you can run the deployment script normally:
```bash
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa
```

### Deploy Your Dashboard

```bash
# With SSH key
python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa

# With password
python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --password mypassword

# Without auto-reload
python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa --no-reload
```

---

## Deployment Script

### Features

The Python deployment script provides following features:

- ✅ **Automatic backup** of existing dashboard before deployment
- ✅ **Secure file transfer** via SSH/SFTP
- ✅ **Automatic YAML reload** (optional)
- ✅ **Multiple authentication methods** (SSH key or password)
- ✅ **Cross-platform support** (works on Windows, Linux, Mac)
- ✅ **Detailed error messages** and status updates

### Script Options

```
--host HOST        Home Assistant server hostname or IP (required)
--user USER        SSH username (required)
--key KEY_FILE     Path to SSH private key file
--password PASS    SSH password (alternative to key)
--port PORT        SSH port (default: 22)
--local FILE       Local dashboard file (default: my-dashboard.yaml at repo root)
--remote PATH      Remote path for dashboard (default: /config/lovelace/ui-lovelace.yaml)
--no-reload        Skip automatic YAML config reload
--no-backup        Skip backup of existing dashboard
```

### Usage Examples

```bash
# Basic deployment with SSH key
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa

# Deployment with password
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --password mypassword

# Deploy to custom location
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa \
  --local my-dashboard.yaml --remote /config/lovelace/dashboard-custom.yaml

# Deploy without backup
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --no-backup

# Deploy without auto-reload
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --no-reload
```

---

## YAML Configuration Reload

Reloading YAML configurations allows you to apply changes without restarting Home Assistant. Here are all the methods to reload YAML configs:

### Method 1: Command Line (SSH)

#### For Home Assistant OS (Hass.io)

```bash
# Reload core configuration
hassio homeassistant reload core_config

# Reload all YAML configurations
hassio homeassistant reload all
```

#### For Docker-based Installations

```bash
# Reload core configuration
docker exec homeassistant homeassistant --script reload_core_config

# Reload automation configurations
docker exec homeassistant homeassistant --script reload automation

# Reload scene configurations
docker exec homeassistant homeassistant --script reload scene

# Reload script configurations
docker exec homeassistant homeassistant --script reload script
```

#### For Virtual Environment Installations

```bash
# Reload core configuration
sudo -u homeassistant -H /srv/homeassistant/bin/homeassistant --script reload_core_config

# Reload specific components
sudo -u homeassistant -H /srv/homeassistant/bin/homeassistant --script reload automation
sudo -u homeassistant -H /srv/homeassistant/bin/homeassistant --script reload scene
sudo -u homeassistant -H /srv/homeassistant/bin/homeassistant --script reload script
```

### Method 2: Home Assistant Web UI

1. Navigate to **Settings** → **Server Controls**
2. Find **YAML Configuration Reloading** section
3. Click on the component you want to reload:
   - **Core Configuration** - Reloads `configuration.yaml`
   - **Automation** - Reloads all automation YAML files
   - **Scene** - Reloads scene configurations
   - **Script** - Reloads script configurations
   - **Group** - Reloads group configurations

### Method 3: Developer Tools

1. Navigate to **Developer Tools** → **Services**
2. Call the `homeassistant.reload_core_config` service
3. For specific components:
   - `automation.reload`
   - `scene.reload`
   - `script.reload`
   - `group.reload`
   - `homeassistant.reload_all`

### Method 4: Using Home Assistant API

```bash
# Reload core configuration via API
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8123/api/services/homeassistant/reload_core_config

# Reload automations
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8123/api/services/automation/reload
```

### Method 5: Using MCP Server (Home Assistant)

If you have the Home Assistant MCP server enabled, you can use it programmatically:

```python
# Example using MCP
import mcp

# Connect to Home Assistant MCP server
client = mcp.Client("home-assistant")

# Reload YAML configurations
client.call_tool("reload_core_config")
```

### What Gets Reloaded?

When you reload YAML configurations:

- ✅ **Core config** - `configuration.yaml`, `automations.yaml`, `scenes.yaml`, `scripts.yaml`
- ✅ **Custom components** - Custom integrations that support reload
- ✅ **Automations** - All automation YAML files
- ✅ **Scenes** - Scene configurations
- ✅ **Scripts** - Script configurations
- ✅ **Groups** - Group definitions

### What Does NOT Get Reloaded?

- ❌ **Platform configurations** (e.g., `mqtt:`, `sensor:`, `switch:` sections in `configuration.yaml`)
- ❌ **Integration configurations** that require restart
- ❌ **HACS custom cards** (needs browser refresh)
- ❌ **Lovelace dashboard changes** (needs browser refresh or UI reload)

### When to Restart Instead of Reload

You need to **restart Home Assistant** (not just reload) when:

- Changing platform configurations (mqtt, sensor, switch, etc.)
- Adding or removing integrations
- Modifying `packages:` sections
- Changes to `homeassistant:` configuration
- Updating core settings that require restart

```bash
# Restart Home Assistant via SSH
hassio homeassistant restart

# Or via Docker
docker restart homeassistant
```

---

## SSH Setup

### Setting up SSH Access to Home Assistant

#### For Home Assistant OS

1. Enable SSH in the Home Assistant UI:
   - Settings → System → Network → Enable SSH
   - Set a password or upload your public SSH key

2. Find your Home Assistant IP address:
   - Settings → System → Network

3. Test SSH connection:
   ```bash
   ssh root@<your-ha-ip>
   ```

#### For Docker-based Installations

1. SSH into your host machine
2. Find the Home Assistant container:
   ```bash
   docker ps | grep homeassistant
   ```

3. Access the container:
   ```bash
   docker exec -it homeassistant bash
   ```

### SSH Key Authentication (Recommended)

1. Generate an SSH key pair (if you don't have one):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "homeassistant"
   ```

2. Copy the public key to Home Assistant:
   ```bash
   ssh-copy-id root@<your-ha-ip>
   ```

3. Test the connection:
   ```bash
   ssh -i ~/.ssh/id_rsa root@<your-ha-ip>
   ```

### Common SSH Paths

| Installation Type | Config Path | Dashboard Path |
|-------------------|-------------|----------------|
| Home Assistant OS | `/config` | `/config/lovelace/ui-lovelace.yaml` |
| Docker | `/config` | `/config/lovelace/ui-lovelace.yaml` |
| Virtual Environment | `/home/homeassistant/.homeassistant` | `/home/homeassistant/.homeassistant/lovelace/ui-lovelace.yaml` |

---

## Troubleshooting

### Connection Issues

**Problem**: "Connection refused" or "Unable to connect"

**Solutions**:
1. Verify Home Assistant is running
2. Check SSH is enabled: Settings → System → Network
3. Verify correct IP address and port
4. Check firewall settings

**Problem**: "Permission denied"

**Solutions**:
1. Verify correct username (often `root` for Home Assistant OS)
2. Check password or SSH key is correct
3. Ensure SSH key permissions are correct:
   ```bash
   chmod 600 ~/.ssh/id_rsa
   ```

### Deployment Issues

**Problem**: "Upload failed"

**Solutions**:
1. Check local file exists and is readable
2. Verify remote directory exists and is writable
3. Ensure you have sufficient disk space
4. Check file permissions on remote server

**Problem**: Dashboard not updating after deployment

**Solutions**:
1. Check if YAML reload was successful
2. Refresh your browser (Ctrl+F5 or Cmd+Shift+R)
3. Check Home Assistant logs for errors:
   - Settings → System → Logs
4. Validate YAML syntax:
   ```bash
   # Using Python
   python -c "import yaml; yaml.safe_load(open('my-dashboard.yaml'))"
   ```

### YAML Reload Issues

**Problem**: "Could not auto-reload configuration"

**Solutions**:
1. Try manual reload commands (see [YAML Configuration Reload](#yaml-configuration-reload))
2. Check Home Assistant logs for specific errors
3. Ensure YAML syntax is valid
4. Some changes require restart, not reload

**Problem**: "Configuration validation error"

**Solutions**:
1. Check YAML indentation
2. Verify no duplicate keys
3. Use a YAML linter: `yamllint my-dashboard.yaml`
4. Test in Home Assistant UI:
   - Settings → YAML Configuration → Validate

### Python Script Issues

**Problem**: "ModuleNotFoundError: No module named 'paramiko'"

**Solution**:
```bash
pip install paramiko
```

**Problem**: Script runs slowly

**Solutions**:
1. Use SSH key authentication instead of password
2. Check network latency to Home Assistant server
3. Increase timeout in script if needed

---

## Advanced Usage

### Multiple Dashboards

Deploy different dashboards by specifying different remote paths:

```bash
# Main dashboard
python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa \
  --local my-dashboard.yaml --remote /config/lovelace/ui-lovelace.yaml

# Custom dashboard
python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa \
  --local my-dashboard.yaml --remote /config/lovelace/dashboard-custom.yaml
```

### Deployment with Validation

Add YAML validation before deployment:

```bash
# Validate YAML first
python -c "import yaml; yaml.safe_load(open('my-dashboard.yaml'))"

# Deploy if validation passes
if [ $? -eq 0 ]; then
    python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa
fi
```

### Automated Deployment with Git

Create a simple deployment workflow:

```bash
#!/bin/bash
# deploy.sh - Simple deployment script

# Pull latest changes
git pull origin main

# Validate YAML
python -c "import yaml; yaml.safe_load(open('my-dashboard.yaml'))"
if [ $? -ne 0 ]; then
    echo "YAML validation failed!"
    exit 1
fi

# Deploy
python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa
```

### Monitoring Deployment

Add logging to track deployments:

```bash
# Deploy with timestamp and logging
echo "[$(date)] Deploying dashboard..." >> deployment.log
python deploy/deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa 2>&1 | tee -a deployment.log
```

---

## Security Best Practices

1. **Use SSH key authentication** instead of passwords
2. **Limit SSH access** to specific IP addresses
3. **Use sudo** only when necessary
4. **Keep backups** of your configurations
5. **Validate YAML** before deployment
6. **Test changes** in a development environment first
7. **Review logs** after each deployment
8. **Use version control** (Git) for your YAML files

---

## Additional Resources

- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [Lovelace Documentation](https://www.home-assistant.io/lovelace/)
- [YAML Configuration](https://www.home-assistant.io/docs/configuration/)
- [SSH Configuration](https://www.home-assistant.io/docs/configuration/yaml/)
- [Home Assistant API](https://developers.home-assistant.io/docs/api/)
- [Home Assistant Community](https://community.home-assistant.io/)

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review Home Assistant logs: Settings → System → Logs
3. Search the [Home Assistant Community](https://community.home-assistant.io/)
4. Check the [Home Assistant GitHub Issues](https://github.com/home-assistant/home-assistant/issues)

---

## License

This deployment script is provided as-is for managing Home Assistant dashboards.