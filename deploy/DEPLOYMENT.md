# Home Assistant Dashboard Deployment Guide

This guide explains how to deploy your Home Assistant dashboard using the Python script and how to reload YAML configurations via command line.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Deployment Script](#deployment-script)
3. [Staging & Promotion Workflow](#staging--promotion-workflow)
4. [YAML Configuration Reload](#yaml-configuration-reload)
5. [SSH Setup](#ssh-setup)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

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
# Stage → verify → promote (recommended workflow)
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --stage
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --promote --token YOUR_TOKEN
```

> See [Usage Examples](#usage-examples) for all deployment modes.

---

## Deployment Script

### Features

The Python deployment script provides following features:

- ✅ **Staging/production workflow** (`--stage` and `--promote` flags)
- ✅ **Automatic backup** of existing files before deployment
- ✅ **Dashboard + theme deployment** (theme via `--theme`, `--stage`, or `--promote`)
- ✅ **In-memory theme name replacement** for staging (local files never modified)
- ✅ **Secure file transfer** via SSH/SFTP
- ✅ **Automatic YAML reload** via HA REST API (`--token`) or CLI fallbacks
- ✅ **Multiple authentication methods** (SSH key or password, RSA/Ed25519/ECDSA)
- ✅ **Cross-platform support** (works on Windows, Linux, Mac)
- ✅ **Detailed error messages** and status updates

### Script Options

```
--host HOST              Home Assistant server hostname or IP (required)
--user USER              SSH username (required)
--key KEY_FILE           Path to SSH private key file (RSA, Ed25519, ECDSA)
--password PASS          SSH password (alternative to key)
--port PORT              SSH port (default: 22)
--local FILE             Local dashboard file (default: my-dashboard.yaml at repo root)
--remote PATH            Remote path for dashboard (default: /config/lovelace/my-dashboard.yaml)
--theme                  Also deploy the theme file (production mode only)
--theme-local FILE       Local prod theme file (default: themes/my_dashboard_theme.yaml)
--theme-remote PATH      Remote path for theme (default: /config/themes/my_dashboard_theme.yaml)
--theme-staging-local FILE  Local staging theme file (default: themes/my_dashboard_theme_staging.yaml)
--stage                  Deploy to staging (dashboard + staging theme, mutually exclusive with --promote)
--promote                Promote to production (dashboard + prod theme, mutually exclusive with --stage)
--token TOKEN            HA Long-Lived Access Token (for API-based reload after deploy)
--no-reload              Skip automatic YAML config reload
--no-backup              Skip backup of existing files
```

### Usage Examples

```bash
# Deploy to staging (recommended first step)
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --stage

# Promote to production (after verifying staging)
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --promote

# Direct production deploy (dashboard only)
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa

# Direct production deploy (dashboard + theme)
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --theme

# Deploy with API-based auto-reload (recommended for Docker setups)
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --promote --token YOUR_TOKEN

# Deploy without backup
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --no-backup

# Deploy without auto-reload
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --no-reload
```

---

## Staging & Promotion Workflow

The deploy script supports a staging/production workflow for testing dashboard changes before going live.

### How It Works

- **Two dashboards** on the HA server: "My Dashboard" (prod) and "My Dashboard (Staging)"
- **Two themes**: "My Dashboard Theme" (prod) and "My Dashboard Theme - Staging"
- `--stage` reads the dashboard YAML, replaces theme references in-memory, and uploads to the staging path. The staging filename is derived from `--remote` (e.g. `my-dashboard.yaml` → `my-dashboard-staging.yaml`). Local files are never modified.
- `--promote` deploys local files as-is to production paths (dashboard + prod theme)
- Both flags respect `--remote` for path resolution
- Both dashboards always exist in the HA sidebar

### Deploy to Staging

```bash
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --stage
```

This will:
1. Read `my-dashboard.yaml` and replace all `My Dashboard Theme` references with `My Dashboard Theme - Staging` in memory
2. Upload the modified dashboard to the staging path (derived from `--remote`, e.g. `/config/lovelace/my-dashboard-staging.yaml`)
3. Upload `themes/my_dashboard_theme_staging.yaml` to `/config/themes/`

### Promote to Production

After verifying staging looks correct:

```bash
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --promote
```

This deploys local files as-is (with prod theme name) to production paths, including the theme file. Staging remains untouched for comparison.

### Typical Workflow

1. Make changes locally to `my-dashboard.yaml` and/or `themes/my_dashboard_theme.yaml`
2. If theme changed, sync changes to `themes/my_dashboard_theme_staging.yaml` (same values, different top-level key)
3. Deploy to staging: `--stage`
4. Open HA sidebar → "My Dashboard (Staging)" → verify changes
5. Promote to production: `--promote`
6. Verify production dashboard
7. Tag the release: `git tag -a live-vN -m "description"`

### One-Time Setup

Add staging dashboard entry to your HA server's `configuration.yaml`:

```yaml
lovelace:
  mode: storage
  dashboards:
    lovelace-yaml:
      mode: yaml
      filename: lovelace/my-dashboard.yaml
      title: My Dashboard
      icon: mdi:view-dashboard
      show_in_sidebar: true
    lovelace-staging:
      mode: yaml
      filename: lovelace/my-dashboard-staging.yaml
      title: My Dashboard (Staging)
      icon: mdi:flask
      show_in_sidebar: true
```

Then restart Home Assistant (required for `lovelace:` config changes).

---

## YAML Configuration Reload

Reloading YAML configurations allows you to apply changes without restarting Home Assistant.

### Automatic Reload via Deploy Script

The deploy script can auto-reload HA after deployment. Pass `--token` with a Long-Lived Access Token:

```bash
python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --promote --token YOUR_TOKEN
```

To create a token: **HA UI → Profile → Security → Long-Lived Access Tokens → Create Token**

The script tries these methods in order:
1. **HA REST API** (if `--token` provided) — works with any install type including Docker with host networking
2. **hassio CLI** — for Home Assistant OS
3. **homeassistant --script** — for venv installs
4. **docker exec** — for Docker installs

Use `--no-reload` to skip auto-reload entirely.

> **Important:** Which reload methods work depends on where you SSH into:
>
> | SSH target | `--remote` path | Reload that works |
> |------------|----------------|-------------------|
> | HA OS / container directly | `/config/lovelace/...` | CLI commands (hassio, docker exec) |
> | Host machine running Docker | Volume mount path (e.g. `/home/user/ha/config/lovelace/...`) | **REST API (`--token`) only** — CLI commands run on the host, not inside the container |
>
> If you SSH into the host machine (not the container), always use `--token` for auto-reload.

### Manual Reload Methods

#### Method 1: Command Line (SSH)

> **Note:** These commands only work when run **inside** the HA container or on HA OS — not from the host machine. If you SSH into the host, use the REST API (Method 4) or the deploy script's `--token` flag instead.

##### For Home Assistant OS (Hass.io)

```bash
# Reload core configuration
hassio homeassistant reload core_config

# Reload all YAML configurations
hassio homeassistant reload all
```

##### For Docker-based Installations

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

##### For Virtual Environment Installations

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

### Method 3: Using Home Assistant API

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
- ❌ **Lovelace dashboard changes** (needs browser refresh — the deploy script handles this automatically via Browser Mod if `--token` is provided)

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

| Installation Type | Config Path | Notes |
|-------------------|-------------|-------|
| Home Assistant OS | `/config` | SSH directly into HA |
| Docker (SSH to container) | `/config` | Via `docker exec` |
| Docker (SSH to host) | Your volume mount path (e.g. `/home/user/ha/config`) | Use `--remote` with the host path, not `/config` |
| Virtual Environment | `/home/homeassistant/.homeassistant` | Direct SSH |

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

**Problem**: "Upload failed" or "No such file"

**Solutions**:
1. Check local file exists and is readable
2. Verify remote directory exists and is writable
3. Ensure you have sufficient disk space
4. Check file permissions on remote server
5. **Do not use `~` in `--remote` paths** — SFTP does not expand tilde. Use absolute paths (e.g. `/home/user/config/...` instead of `~/config/...`)

**Problem**: "Permission denied" on upload

**Solutions**:
1. Check file/directory ownership on the remote server
2. For Docker setups, directories created by the container may be owned by root. Fix with:
   ```bash
   sudo chown -R youruser:youruser /path/to/ha/config/lovelace /path/to/ha/config/themes
   ```

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
2. **Never commit tokens or passwords** — pass `--token` and `--password` via environment variables or command line, never hardcode in scripts
3. **Limit SSH access** to specific IP addresses
4. **Keep backups** of your configurations
5. **Validate YAML** before deployment
6. **Use the staging workflow** to test changes before going live
7. **Use version control** (Git) for your YAML files

---

## Additional Resources

- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [Lovelace Documentation](https://www.home-assistant.io/lovelace/)
- [YAML Configuration](https://www.home-assistant.io/docs/configuration/)
- [SSH Configuration](https://www.home-assistant.io/docs/configuration/yaml/)
- [Home Assistant API](https://developers.home-assistant.io/docs/api/)
- [Home Assistant Community](https://community.home-assistant.io/)

---

## License

This deployment script is provided as-is for managing Home Assistant dashboards.