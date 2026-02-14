#!/usr/bin/env python3
"""
Home Assistant Dashboard Deployment Script

This script deploys the new dashboard YAML file to your Home Assistant server
and optionally reloads the YAML configuration.

Usage:
    python deploy_dashboard.py [--host HOST] [--user USER] [--key KEY] [--port PORT] [--no-reload]

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
    DEFAULT_DASHBOARD_FILE = "ui-lovelace.yaml"
    
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
                key = paramiko.RSAKey.from_private_key_file(self.key_file)
                self.ssh_client.connect(
                    hostname=self.host,
                    username=self.username,
                    pkey=key,
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
    
    def deploy_dashboard(self, local_file, remote_path):
        """
        Deploy dashboard file to Home Assistant
        
        Args:
            local_file: Path to local dashboard YAML file
            remote_path: Path on remote server where dashboard should be saved
        """
        try:
            # Ensure local file exists
            if not os.path.exists(local_file):
                raise FileNotFoundError(f"Local file not found: {local_file}")
            
            # Upload file
            print(f"Uploading {local_file} to {remote_path}...")
            self.sftp_client.put(local_file, remote_path)
            print(f"✓ File uploaded successfully")
            
            return True
            
        except Exception as e:
            print(f"✗ Upload failed: {e}")
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
    
    def backup_existing_dashboard(self, remote_path):
        """Create a backup of the existing dashboard file"""
        try:
            backup_path = f"{remote_path}.backup"
            print(f"Creating backup of existing dashboard...")
            
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
    parser = argparse.ArgumentParser(
        description="Deploy Home Assistant dashboard via SSH",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy with SSH key
  python deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa
  
  # Deploy with password
  python deploy_dashboard.py --host 192.168.1.100 --user homeassistant --password mypassword
  
  # Deploy without auto-reload
  python deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa --no-reload
  
  # Deploy custom dashboard file to custom location
  python deploy_dashboard.py --host 192.168.1.100 --user homeassistant --key ~/.ssh/id_rsa \\
                              --local new.dashboard.yaml --remote /config/lovelace/ui-lovelace.yaml
        """
    )
    
    parser.add_argument('--host', required=True, help='Home Assistant server hostname or IP')
    parser.add_argument('--user', required=True, help='SSH username')
    parser.add_argument('--key', help='Path to SSH private key file')
    parser.add_argument('--password', help='SSH password (alternative to key)')
    parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('--local', default='new.dashboard.yaml', 
                       help='Local dashboard file to deploy (default: new.dashboard.yaml)')
    parser.add_argument('--remote', 
                       help='Remote path for dashboard file (default: /config/lovelace/ui-lovelace.yaml)')
    parser.add_argument('--no-reload', action='store_true',
                       help='Skip automatic YAML config reload')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup of existing dashboard')
    
    args = parser.parse_args()
    
    # Validate authentication method
    if not args.key and not args.password:
        print("Error: Must specify either --key or --password for authentication")
        sys.exit(1)
    
    # Set default remote path
    if not args.remote:
        args.remote = f"{HomeAssistantDeployer.DEFAULT_DASHBOARDS_DIR}/{HomeAssistantDeployer.DEFAULT_DASHBOARD_FILE}"
    
    # Validate local file
    if not os.path.exists(args.local):
        print(f"Error: Local file not found: {args.local}")
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
        # Backup existing dashboard
        if not args.no_backup:
            deployer.backup_existing_dashboard(args.remote)
        
        # Deploy new dashboard
        if deployer.deploy_dashboard(args.local, args.remote):
            print("\n" + "="*60)
            print("✓ Dashboard deployed successfully!")
            print("="*60)
            
            # Reload configuration
            if not args.no_reload:
                deployer.reload_yaml_config()
            else:
                print("\nNote: Automatic reload skipped. To reload YAML configs:")
                print("  - Via UI: Settings → Server Controls → YAML Configuration Reloading")
                print("  - Via SSH: hassio homeassistant reload core_config")
        else:
            print("\n✗ Deployment failed")
            sys.exit(1)
            
    finally:
        deployer.disconnect()


if __name__ == "__main__":
    main()