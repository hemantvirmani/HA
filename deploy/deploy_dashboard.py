#!/usr/bin/env python3
"""
Home Assistant Dashboard Deployment Script

This script deploys the dashboard YAML file and optionally the theme file
to your Home Assistant server, and reloads the YAML configuration.

Usage:
    python deploy/deploy_dashboard.py [--host HOST] [--user USER] [--key KEY] [--port PORT] [--no-reload]
    python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --theme

Requirements:
    - Python 3.6+
    - Paramiko library (pip install paramiko)
"""

import argparse
import sys
import os
from pathlib import Path
import paramiko

class HomeAssistantDeployer:
    """Handles deployment to Home Assistant server via SSH"""
    
    # Default Home Assistant configuration paths
    DEFAULT_HA_CONFIG_DIR = "/config"
    DEFAULT_DASHBOARDS_DIR = "/config/lovelace"
    DEFAULT_DASHBOARD_FILE = "my-dashboard.yaml"
    DEFAULT_THEMES_DIR = "/config/themes"
    
    def __init__(self, host, username, key_file=None, password=None, port=22):
        """
        Initialize the deployer
        
        Args:
            host: SSH hostname or IP address
            username: SSH username
            key_file: Path to SSH private key file (optional)
            password: SSH password (alternative to key_file)
            port: SSH port (default: 22)
        """
        self.host = host
        self.username = username
        self.key_file = key_file
        self.password = password
        self.port = port
        self.ssh_client = None
        self.sftp_client = None
        
    def connect(self):
        """Establish SSH connection"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_file:
                self.ssh_client.connect(
                    hostname=self.host,
                    username=self.username,
                    key_filename=self.key_file,
                    port=self.port
                )
            else:
                self.ssh_client.connect(
                    hostname=self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port
                )
            
            self.sftp_client = self.ssh_client.open_sftp()
            print(f"✓ Connected to {self.host}")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
        print("✓ Disconnected from server")
    
    def deploy_file(self, local_file, remote_path, label="file"):
        """
        Deploy a file to Home Assistant

        Args:
            local_file: Path to local file
            remote_path: Path on remote server
            label: Display label for status messages (e.g. "dashboard", "theme")
        """
        try:
            if not os.path.exists(local_file):
                raise FileNotFoundError(f"Local file not found: {local_file}")

            print(f"Uploading {label}: {local_file} → {remote_path}...")
            self.sftp_client.put(local_file, remote_path)
            print(f"✓ {label.capitalize()} uploaded successfully")

            return True

        except Exception as e:
            print(f"✗ {label.capitalize()} upload failed: {e}")
            return False
    
    def reload_yaml_config(self):
        """
        Reload YAML configuration in Home Assistant using command line
        
        This uses the Home Assistant CLI to reload the configuration
        """
        try:
            print("Reloading Home Assistant YAML configuration...")
            
            # Method 1: Using hassio CLI (if running Hass.io/Home Assistant OS)
            commands = [
                # Try hassio CLI first (Home Assistant OS)
                "hassio homeassistant reload core_config",
                # Fallback to direct homeassistant command
                "sudo -u homeassistant -H /srv/homeassistant/bin/homeassistant --script reload_core_config",
                # Another fallback for container-based installs
                "docker exec homeassistant homeassistant --script reload_core_config"
            ]
            
            success = False
            for cmd in commands:
                try:
                    stdin, stdout, stderr = self.ssh_client.exec_command(cmd, timeout=30)
                    exit_status = stdout.channel.recv_exit_status()
                    
                    if exit_status == 0:
                        print(f"✓ Configuration reloaded successfully using: {cmd}")
                        success = True
                        break
                except Exception:
                    continue
            
            if not success:
                print("⚠ Could not auto-reload configuration. You may need to reload manually:")
                print("  - Via UI: Settings → Server Controls → YAML Configuration Reloading")
                print("  - Via SSH: Run one of the commands above manually")
            
            return success
            
        except Exception as e:
            print(f"✗ Reload failed: {e}")
            return False
    
    def backup_file(self, remote_path, label="file"):
        """Create a backup of an existing remote file"""
        try:
            backup_path = f"{remote_path}.backup"
            print(f"Creating backup of existing {label}...")

            stdin, stdout, stderr = self.ssh_client.exec_command(
                f"test -f {remote_path} && cp {remote_path} {backup_path} || echo 'No existing file to backup'"
            )
            stdout.read()  # Wait for command to complete

            print(f"✓ Backup created at {backup_path}")
            return True

        except Exception as e:
            print(f"⚠ Backup warning: {e}")
            return False


def main():
    # Resolve paths relative to script location (repo root)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    default_local = str(repo_root / "my-dashboard.yaml")
    default_theme_local = str(repo_root / "themes" / "my_dashboard_theme.yaml")

    parser = argparse.ArgumentParser(
        description="Deploy Home Assistant dashboard and theme via SSH",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy dashboard only
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa

  # Deploy dashboard + theme
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --theme

  # Deploy with password
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --password mypassword --theme

  # Deploy without auto-reload
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --no-reload

  # Deploy with custom paths
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa \\
      --local my-dashboard.yaml --remote /config/lovelace/ui-lovelace.yaml \\
      --theme --theme-local themes/my_dashboard_theme.yaml --theme-remote /config/themes/my_dashboard_theme.yaml
        """
    )

    parser.add_argument('--host', required=True, help='Home Assistant server hostname or IP')
    parser.add_argument('--user', required=True, help='SSH username')
    parser.add_argument('--key', help='Path to SSH private key file (RSA, Ed25519, ECDSA)')
    parser.add_argument('--password', help='SSH password (alternative to key)')
    parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('--local', default=default_local,
                       help=f'Local dashboard file (default: my-dashboard.yaml at repo root)')
    parser.add_argument('--remote',
                       help='Remote path for dashboard file (default: /config/lovelace/ui-lovelace.yaml)')
    parser.add_argument('--theme', action='store_true',
                       help='Also deploy the theme file')
    parser.add_argument('--theme-local', default=default_theme_local,
                       help='Local theme file (default: themes/my_dashboard_theme.yaml)')
    parser.add_argument('--theme-remote',
                       help='Remote path for theme file (default: /config/themes/my_dashboard_theme.yaml)')
    parser.add_argument('--no-reload', action='store_true',
                       help='Skip automatic YAML config reload')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup of existing files')

    args = parser.parse_args()

    # Validate authentication method
    if not args.key and not args.password:
        print("Error: Must specify either --key or --password for authentication")
        sys.exit(1)

    # Set default remote paths
    if not args.remote:
        args.remote = f"{HomeAssistantDeployer.DEFAULT_DASHBOARDS_DIR}/{HomeAssistantDeployer.DEFAULT_DASHBOARD_FILE}"
    if not args.theme_remote:
        theme_filename = os.path.basename(args.theme_local)
        args.theme_remote = f"{HomeAssistantDeployer.DEFAULT_THEMES_DIR}/{theme_filename}"

    # Validate local files
    if not os.path.exists(args.local):
        print(f"Error: Local dashboard file not found: {args.local}")
        sys.exit(1)
    if args.theme and not os.path.exists(args.theme_local):
        print(f"Error: Local theme file not found: {args.theme_local}")
        sys.exit(1)

    # Deploy
    deployer = HomeAssistantDeployer(
        host=args.host,
        username=args.user,
        key_file=args.key,
        password=args.password,
        port=args.port
    )

    if not deployer.connect():
        sys.exit(1)

    try:
        # --- Deploy dashboard ---
        if not args.no_backup:
            deployer.backup_file(args.remote, "dashboard")

        if not deployer.deploy_file(args.local, args.remote, "dashboard"):
            print("\n✗ Dashboard deployment failed")
            sys.exit(1)

        # --- Deploy theme (if requested) ---
        if args.theme:
            print()  # blank line separator
            if not args.no_backup:
                deployer.backup_file(args.theme_remote, "theme")

            if not deployer.deploy_file(args.theme_local, args.theme_remote, "theme"):
                print("\n✗ Theme deployment failed")
                sys.exit(1)

        # --- Summary ---
        print("\n" + "="*60)
        deployed = ["dashboard"]
        if args.theme:
            deployed.append("theme")
        print(f"✓ Deployed successfully: {', '.join(deployed)}")
        print("="*60)

        # Reload configuration
        if not args.no_reload:
            deployer.reload_yaml_config()
        else:
            print("\nNote: Automatic reload skipped. To reload YAML configs:")
            print("  - Via UI: Settings → Server Controls → YAML Configuration Reloading")
            print("  - Via SSH: hassio homeassistant reload core_config")

    finally:
        deployer.disconnect()


if __name__ == "__main__":
    main()