# routes/network_routes.py
"""
Contains routes for managing the device's network connectivity (Wi-Fi).
"""
from flask import Blueprint, jsonify, request
import subprocess
import platform
import time

network_bp = Blueprint('network_bp', __name__)

def is_linux():
    """Checks if the current operating system is Linux."""
    return platform.system() == "Linux"

def restart_hotspot():
    """
    Attempts to restart the NetworkManager hotspot connection after a failed attempt.
    NOTE: The connection name 'BantayTubig-Hotspot' must match the name 
    configured in NetworkManager on the device.
    """
    try:
        print("--- WiFi connection failed. Attempting to restart hotspot... ---")
        # This command reactivates the hotspot connection profile.
        subprocess.run(
            ['sudo', 'nmcli', 'con', 'up', 'BantayTubig-Hotspot'],
            check=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        print("--- Hotspot restarted successfully. ---")
    except Exception as e:
        print(f"!!! CRITICAL: FAILED TO RESTART HOTSPOT: {e} !!!")

def parse_nmcli_scan_output(output):
    """
    Parses the reliable, machine-readable (terse) output from nmcli.
    """
    networks = []
    lines = output.strip().split('\n')
    for line in lines:
        if not line: continue
        parts = [p.replace('\\:', ':') for p in line.split(':')]
        if len(parts) >= 5:
            try:
                signal_strength = int(parts[2])
                networks.append({
                    'in_use': parts[0] == '*',
                    'ssid': parts[1],
                    'signal': signal_strength,
                    'rate': parts[3],
                    'security': parts[4] if len(parts[4]) > 0 else 'Open'
                })
            except (ValueError, IndexError):
                continue
    return networks

@network_bp.route('/system/network/status', methods=['GET'])
def get_network_status():
    """
    Gets the current network connection status, reliably fetching the correct SSID.
    """
    if not is_linux():
        return jsonify({
            'connected_ssid': 'SimulatedWiFi',
            'ip_address': '192.168.1.100',
            'status': 'connected'
        })
    try:
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'ACTIVE,SSID,DEVICE', 'dev', 'wifi'],
            check=True, capture_output=True, text=True
        )
        active_connections = result.stdout.strip().split('\n')

        ssid = None
        wifi_device = None
        for conn in active_connections:
            parts = conn.split(':')
            if len(parts) >= 3 and parts[0] == 'yes':
                ssid = parts[1].replace('\\:', ':')
                wifi_device = parts[2]
                break 

        if not wifi_device:
            return jsonify({'status': 'disconnected'})

        ip_result = subprocess.run(
            ['nmcli', '-t', '-f', 'IP4.ADDRESS', 'd', 'show', wifi_device],
            check=True, capture_output=True, text=True
        )
        ip_address = ip_result.stdout.strip().split(':')[1].split('/')[0] if ':' in ip_result.stdout else 'Acquiring...'

        return jsonify({
            'connected_ssid': ssid,
            'ip_address': ip_address,
            'status': 'connected'
        })
    except Exception:
        return jsonify({'status': 'disconnected'})

@network_bp.route('/system/network/scan', methods=['POST'])
def scan_wifi_networks():
    """Scans for available Wi-Fi networks."""
    if not is_linux():
        return jsonify([
            {'in_use': True, 'ssid': 'Home_WiFi', 'signal': 95, 'rate': '150 Mbit/s', 'security': 'WPA2'},
        ])
    try:
        subprocess.run(['sudo', 'nmcli', 'dev', 'wifi', 'rescan'], check=True, timeout=10)
        time.sleep(5)
        result = subprocess.run(
            ['nmcli', '-t', '-e', 'no', '-f', 'IN-USE,SSID,SIGNAL,RATE,SECURITY', 'dev', 'wifi', 'list'],
            check=True, capture_output=True, text=True
        )
        networks = parse_nmcli_scan_output(result.stdout)
        return jsonify(networks)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return jsonify({'status': 'error', 'message': f"Failed to scan networks: {e}"}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@network_bp.route('/system/network/connect', methods=['POST'])
def connect_to_wifi():
    """Connects to a specified Wi-Fi network and restarts hotspot on failure."""
    if not is_linux():
        return jsonify({'status': 'success', 'message': 'Simulated connection successful.'})
    
    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password')
    if not ssid:
        return jsonify({'status': 'error', 'message': 'SSID is required.'}), 400
    try:
        command = ['sudo', 'nmcli', 'dev', 'wifi', 'connect', ssid]
        if password:
            command.extend(['password', password])
        # This will block until the connection succeeds or fails
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
        # If the command succeeds, we send a success message. The browser will disconnect.
        return jsonify({'status': 'success', 'message': result.stdout.strip()})
    except subprocess.CalledProcessError as e:
        restart_hotspot() # Restart hotspot on failure
        error_message = "Connection failed: The password may be incorrect."
        return jsonify({'status': 'error', 'message': error_message}), 500
    except subprocess.TimeoutExpired:
        restart_hotspot() # Restart hotspot on failure
        return jsonify({'status': 'error', 'message': 'Connection timed out.'}), 500
    except Exception as e:
        restart_hotspot() # Restart hotspot on any other failure
        return jsonify({'status': 'error', 'message': str(e)}), 500