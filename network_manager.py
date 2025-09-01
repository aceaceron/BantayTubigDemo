# network_manager.py
import subprocess
import time
import platform

# --- Configuration ---
HOTSPOT_SSID = "BantayTubig-Setup"
HOTSPOT_PASS = "bantaytubig"
HOTSPOT_CONNECTION_NAME = "BantayTubig-Hotspot"
WIFI_IFACE = "wlan0"

def is_linux():
    """Checks if the current operating system is Linux."""
    return platform.system() == "Linux"

def run_command(command, ignore_errors=False):
    """A helper to run shell commands with sudo."""
    try:
        full_command = ['sudo'] + command
        result = subprocess.run(
            full_command, check=not ignore_errors, capture_output=True,
            text=True, shell=False, timeout=15
        )
        if result.returncode != 0 and not ignore_errors:
            print(f"Command failed: {' '.join(command)}\nError: {result.stderr.strip()}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Command exception: {' '.join(command)}\nError: {e}")
        return None

def check_wifi_connection():
    """
    Checks for an active WiFi connection by directly checking if the wlan0
    interface has been assigned an IP address by a router.
    """
    if not is_linux(): return True
    output = run_command(['ip', '-4', 'addr', 'show', WIFI_IFACE], ignore_errors=True)
    if output:
        for line in output.split('\n'):
            if 'inet' in line and 'global' in line:
                ip_address = line.strip().split()[1].split('/')[0]
                print(f"Found active IP address on {WIFI_IFACE}: {ip_address}")
                if not ip_address.startswith("10.42.0."):
                    return True
    print("No active client WiFi connection found.")
    return False

def is_client_connected():
    """Checks if at least one client is connected to our hotspot using 'iw'."""
    if not is_linux(): return True
    output = run_command(['iw', 'dev', WIFI_IFACE, 'station', 'dump'])
    return bool(output)

def start_hotspot():
    """
    Starts a robust WiFi hotspot by ensuring a clean state before creation.
    """
    if not is_linux(): return True

    print("Starting hotspot setup...")

    # --- CRITICAL FIX V3: Force the device into a known good state ---
    print("1. Forcing WiFi radio on and setting device to managed mode...")
    run_command(['nmcli', 'radio', 'wifi', 'on'], ignore_errors=True)
    run_command(['nmcli', 'device', 'set', WIFI_IFACE, 'managed', 'yes'], ignore_errors=True)
    time.sleep(2) # Give a moment for the device to settle

    # 2. Clean up any previous hotspot attempts first.
    print("2. Deleting any old hotspot profiles...")
    run_command(['nmcli', 'con', 'delete', HOTSPOT_CONNECTION_NAME], ignore_errors=True)
    time.sleep(1)

    # 3. Disconnect the interface to ensure it's available.
    print("3. Disconnecting WiFi interface to ensure it's free...")
    run_command(['nmcli', 'dev', 'disconnect', WIFI_IFACE], ignore_errors=True)
    time.sleep(2)

    # 4. Now, create the hotspot profile from scratch.
    print(f"4. Creating new hotspot profile '{HOTSPOT_CONNECTION_NAME}'...")
    run_command([
        'nmcli', 'con', 'add', 'type', 'wifi', 'ifname', WIFI_IFACE,
        'con-name', HOTSPOT_CONNECTION_NAME, 'autoconnect', 'no', 'ssid', HOTSPOT_SSID
    ])
    run_command(['nmcli', 'con', 'modify', HOTSPOT_CONNECTION_NAME, '802-11-wireless.mode', 'ap'])
    run_command(['nmcli', 'con', 'modify', HOTSPOT_CONNECTION_NAME, 'ipv4.method', 'shared'])
    run_command(['nmcli', 'con', 'modify', HOTSPOT_CONNECTION_NAME, 'wifi-sec.key-mgmt', 'wpa-psk'])
    run_command(['nmcli', 'con', 'modify', HOTSPOT_CONNECTION_NAME, 'wifi-sec.psk', HOTSPOT_PASS])

    # 5. Attempt to activate the newly created connection.
    print("5. Activating hotspot...")
    output = run_command(['nmcli', 'con', 'up', HOTSPOT_CONNECTION_NAME])

    if output and "successfully activated" in output:
        print("Hotspot started successfully.")
        return True
    else:
        print("Failed to start hotspot. Cleaning up profile again.")
        run_command(['nmcli', 'con', 'delete', HOTSPOT_CONNECTION_NAME], ignore_errors=True)
        return False

def stop_hotspot():
    """Stops the hotspot and deletes its connection profile."""
    if not is_linux(): return
    print("Stopping and deleting hotspot connection profile...")
    run_command(['nmcli', 'con', 'down', HOTSPOT_CONNECTION_NAME], ignore_errors=True)
    run_command(['nmcli', 'con', 'delete', HOTSPOT_CONNECTION_NAME], ignore_errors=True)
    print("Hotspot stopped and profile deleted.")
