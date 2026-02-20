#!/usr/bin/env python3
"""
Home Assistant Dashboard Deployment Script

Deploys the dashboard YAML and theme to your Home Assistant server via SSH.
Supports staging/production workflow with --stage and --promote flags.

Usage:
    python deploy/deploy_dashboard.py --host HOST --user USER --key KEY          # prod deploy (dashboard only)
    python deploy/deploy_dashboard.py --host HOST --user USER --key KEY --theme  # prod deploy (dashboard + theme)
    python deploy/deploy_dashboard.py --host HOST --user USER --key KEY --stage  # staging deploy
    python deploy/deploy_dashboard.py --host HOST --user USER --key KEY --promote # promote to prod

Requirements:
    - Python 3.6+
    - Paramiko library (pip install paramiko)
"""

import argparse
import io
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

    # Theme names (must match top-level key in theme YAML files)
    PROD_THEME_NAME = "My Dashboard Theme"
    STAGING_THEME_NAME = "My Dashboard Theme - Staging"
    
    def __init__(self, host, username, key_file=None, password=None, port=22, token=None):
        """
        Initialize the deployer

        Args:
            host: SSH hostname or IP address
            username: SSH username
            key_file: Path to SSH private key file (optional)
            password: SSH password (alternative to key_file)
            port: SSH port (default: 22)
            token: Home Assistant Long-Lived Access Token (optional, for API reload)
        """
        self.host = host
        self.username = username
        self.key_file = key_file
        self.password = password
        self.port = port
        self.token = token
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

    def deploy_content(self, content, remote_path, label="file"):
        """
        Deploy in-memory content to Home Assistant (no local file needed).

        Args:
            content: String content to upload
            remote_path: Path on remote server
            label: Display label for status messages
        """
        try:
            print(f"Uploading {label}: → {remote_path}...")
            file_obj = io.BytesIO(content.encode("utf-8"))
            self.sftp_client.putfo(file_obj, remote_path)
            print(f"✓ {label.capitalize()} uploaded successfully")
            return True
        except Exception as e:
            print(f"✗ {label.capitalize()} upload failed: {e}")
            return False

    def reload_yaml_config(self):
        """
        Reload YAML configuration in Home Assistant.

        Tries HA REST API first (if --token provided), then falls back to CLI commands.
        """
        try:
            print("Reloading Home Assistant YAML configuration...")

            # Method 1: HA REST API (works with any install type if token provided)
            if self.token:
                curl_cmd = (
                    f'curl -sf -X POST'
                    f' -H "Authorization: Bearer {self.token}"'
                    f' -H "Content-Type: application/json"'
                    f' http://localhost:8123/api/services/homeassistant/reload_core_config'
                )
                try:
                    stdin, stdout, stderr = self.ssh_client.exec_command(curl_cmd, timeout=30)
                    exit_status = stdout.channel.recv_exit_status()
                    if exit_status == 0:
                        print("✓ Configuration reloaded successfully via HA REST API")
                        self._browser_refresh()
                        return True
                    else:
                        err = stderr.read().decode().strip()
                        print(f"⚠ API reload failed (exit {exit_status}): {err}")
                except Exception as e:
                    print(f"⚠ API reload failed: {e}")

            # Method 2: CLI fallbacks
            commands = [
                "hassio homeassistant reload core_config",
                "sudo -u homeassistant -H /srv/homeassistant/bin/homeassistant --script reload_core_config",
                "docker exec homeassistant homeassistant --script reload_core_config"
            ]

            for cmd in commands:
                try:
                    stdin, stdout, stderr = self.ssh_client.exec_command(cmd, timeout=30)
                    exit_status = stdout.channel.recv_exit_status()
                    if exit_status == 0:
                        print(f"✓ Configuration reloaded successfully using: {cmd}")
                        return True
                except Exception:
                    continue

            print("⚠ Could not auto-reload configuration. You may need to reload manually:")
            print("  - Via UI: Settings → Server Controls → YAML Configuration Reloading")
            return False

        except Exception as e:
            print(f"✗ Reload failed: {e}")
            return False
    
    def _browser_refresh(self):
        """Refresh all connected browsers via Browser Mod (if installed)."""
        if not self.token:
            return
        curl_cmd = (
            f'curl -sf -X POST'
            f' -H "Authorization: Bearer {self.token}"'
            f' -H "Content-Type: application/json"'
            f' http://localhost:8123/api/services/browser_mod/refresh'
        )
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(curl_cmd, timeout=10)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print("✓ Browser refresh triggered via Browser Mod")
            else:
                print("⚠ Browser Mod refresh skipped (not installed or unavailable)")
        except Exception:
            pass

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
  # Deploy dashboard only (production)
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa

  # Deploy dashboard + theme (production)
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --theme

  # Deploy to staging (dashboard + theme, theme name auto-replaced)
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --stage

  # Promote staging to production (dashboard + theme)
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --promote

  # Deploy without auto-reload
  python deploy/deploy_dashboard.py --host 192.168.1.100 --user root --key ~/.ssh/id_rsa --no-reload
        """
    )

    parser.add_argument('--host', required=True, help='Home Assistant server hostname or IP')
    parser.add_argument('--user', required=True, help='SSH username')
    parser.add_argument('--key', help='Path to SSH private key file (RSA, Ed25519, ECDSA)')
    parser.add_argument('--password', help='SSH password (alternative to key)')
    parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('--local', default=default_local,
                       help='Local dashboard file (default: my-dashboard.yaml at repo root)')
    parser.add_argument('--remote',
                       help='Remote path for dashboard file (default: /config/lovelace/my-dashboard.yaml)')
    parser.add_argument('--theme', action='store_true',
                       help='Also deploy the theme file (production mode only)')
    parser.add_argument('--theme-local', default=default_theme_local,
                       help='Local theme file (default: themes/my_dashboard_theme.yaml)')
    parser.add_argument('--theme-remote',
                       help='Remote path for theme file (default: /config/themes/my_dashboard_theme.yaml)')

    # Staging/promotion mode (mutually exclusive)
    deploy_mode = parser.add_mutually_exclusive_group()
    deploy_mode.add_argument('--stage', action='store_true',
                            help='Deploy to staging (dashboard + staging theme)')
    deploy_mode.add_argument('--promote', action='store_true',
                            help='Promote to production (dashboard + prod theme)')

    parser.add_argument('--token',
                       help='HA Long-Lived Access Token (for API-based reload)')
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
        # Derive theme dir from --remote's parent (e.g. ~/ha/config/lovelace/.. → ~/ha/config/themes/)
        config_dir = os.path.dirname(os.path.dirname(args.remote))
        theme_filename = os.path.basename(args.theme_local)
        args.theme_remote = f"{config_dir}/themes/{theme_filename}"

    # Validate local files
    if not os.path.exists(args.local):
        print(f"Error: Local dashboard file not found: {args.local}")
        sys.exit(1)

    if (args.theme or args.promote) and not os.path.exists(args.theme_local):
        print(f"Error: Local theme file not found: {args.theme_local}")
        sys.exit(1)

    # Deploy
    deployer = HomeAssistantDeployer(
        host=args.host,
        username=args.user,
        key_file=args.key,
        password=args.password,
        port=args.port,
        token=args.token
    )

    if not deployer.connect():
        sys.exit(1)

    try:
        deployed = []

        if args.stage:
            # ── Staging deployment ──
            # Derive staging paths from --remote filename (e.g. foo.yaml → foo-staging.yaml)
            dashboard_dir = os.path.dirname(args.remote)
            theme_dir = os.path.dirname(args.theme_remote)
            remote_name = os.path.basename(args.remote)
            remote_stem, remote_ext = os.path.splitext(remote_name)
            staging_dashboard_remote = (
                f"{dashboard_dir}/{remote_stem}-staging{remote_ext}"
            )
            # Derive staging theme remote path from prod theme filename (foo.yaml → foo-staging.yaml)
            theme_name = os.path.basename(args.theme_remote)
            theme_stem, theme_ext = os.path.splitext(theme_name)
            staging_theme_remote = f"{theme_dir}/{theme_stem}-staging{theme_ext}"

            # Dashboard: replace theme name in-memory
            dashboard_content = Path(args.local).read_text(encoding="utf-8")
            dashboard_content = dashboard_content.replace(
                HomeAssistantDeployer.PROD_THEME_NAME,
                HomeAssistantDeployer.STAGING_THEME_NAME
            )

            if not args.no_backup:
                deployer.backup_file(staging_dashboard_remote, "staging dashboard")

            if not deployer.deploy_content(dashboard_content, staging_dashboard_remote, "staging dashboard"):
                print("\n✗ Staging dashboard deployment failed")
                sys.exit(1)
            deployed.append("staging dashboard")

            # Theme: replace top-level key in-memory (no second file needed)
            print()
            theme_content = Path(args.theme_local).read_text(encoding="utf-8")
            theme_content = theme_content.replace(
                HomeAssistantDeployer.PROD_THEME_NAME + ":",
                HomeAssistantDeployer.STAGING_THEME_NAME + ":",
                1
            )

            if not args.no_backup:
                deployer.backup_file(staging_theme_remote, "staging theme")

            if not deployer.deploy_content(theme_content, staging_theme_remote, "staging theme"):
                print("\n✗ Staging theme deployment failed")
                sys.exit(1)
            deployed.append("staging theme")

        else:
            # ── Production deployment (default or --promote) ──
            if not args.no_backup:
                deployer.backup_file(args.remote, "dashboard")

            if not deployer.deploy_file(args.local, args.remote, "dashboard"):
                print("\n✗ Dashboard deployment failed")
                sys.exit(1)
            deployed.append("dashboard")

            # Deploy theme if --theme or --promote
            if args.theme or args.promote:
                print()
                if not args.no_backup:
                    deployer.backup_file(args.theme_remote, "theme")

                if not deployer.deploy_file(args.theme_local, args.theme_remote, "theme"):
                    print("\n✗ Theme deployment failed")
                    sys.exit(1)
                deployed.append("theme")

        # ── Summary ──
        if args.stage:
            mode_label = "STAGING"
        elif args.promote:
            mode_label = "PROMOTE TO PROD"
        else:
            mode_label = "PRODUCTION"

        print(f"\n{'='*60}")
        print(f"✓ Deployed successfully ({mode_label}): {', '.join(deployed)}")
        print(f"{'='*60}")

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