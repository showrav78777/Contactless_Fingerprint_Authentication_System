import subprocess
import platform
import re
import os

def get_wifi_profiles():
    system = platform.system()
    
    if system == "Windows":
        # Windows implementation (original code)
        try:
            data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding='utf-8')
            profiles = [line.split(":")[1].strip() for line in data.splitlines() if "All User Profile" in line]
            
            for profile in profiles:
                try:
                    results = subprocess.check_output(
                        ['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'], encoding='utf-8'
                    )
                    result_lines = results.splitlines()
                    key = "N/A"
                    for line in result_lines:
                        if "Key Content" in line:
                            key = line.split(":")[1].strip()
                            break
                    print(f"Profile: {profile:<30} | Password: {key:<}")
                except Exception as e:
                    print(f"Error retrieving details for {profile}: {e}")
            
            if not profiles:
                print("No Wi-Fi profiles found.")
                
        except subprocess.CalledProcessError as e:
            print(f"Error running netsh command: {e}")
    
    elif system == "Darwin":  # macOS
        try:
            # First, find the active WiFi interface
            interfaces_output = subprocess.check_output(['networksetup', '-listallhardwareports'], encoding='utf-8')
            wifi_interfaces = []
            
            # Parse the output to find Wi-Fi interfaces
            current_interface = None
            for line in interfaces_output.splitlines():
                if "Hardware Port: Wi-Fi" in line or "Hardware Port: AirPort" in line:
                    current_interface = True
                elif current_interface and "Device:" in line:
                    interface_name = line.split("Device:")[1].strip()
                    wifi_interfaces.append(interface_name)
                    current_interface = False
            
            if not wifi_interfaces:
                print("No Wi-Fi interfaces found.")
                return
                
            print(f"Found Wi-Fi interfaces: {', '.join(wifi_interfaces)}")
            
            # Try each interface
            current_network = None
            for interface in wifi_interfaces:
                try:
                    output = subprocess.check_output(
                        ['networksetup', '-getairportnetwork', interface], encoding='utf-8'
                    )
                    if "Current Wi-Fi Network" in output:
                        current_network = output.split(': ')[1].strip()
                        active_interface = interface
                        break
                except (subprocess.CalledProcessError, IndexError):
                    continue
            
            if current_network:
                print(f"Current Wi-Fi network: {current_network} (on {active_interface})")
                
                # List all preferred networks for the active interface
                try:
                    networks = subprocess.check_output(
                        ['networksetup', '-listpreferredwirelessnetworks', active_interface], 
                        encoding='utf-8'
                    ).splitlines()[1:]  # Skip the first line which is a header
                    
                    print("\nSaved Wi-Fi networks:")
                    for network in networks:
                        network = network.strip()
                        if network:  # Skip empty lines
                            print(f"Profile: {network:<30} | Password: [Requires admin privileges]")
                except subprocess.CalledProcessError as e:
                    print(f"Error listing preferred networks: {e}")
            else:
                # Alternative method using airport command
                try:
                    airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
                    if os.path.exists(airport_path):
                        output = subprocess.check_output([airport_path, '-I'], encoding='utf-8')
                        ssid_match = re.search(r' SSID: (.+)$', output, re.MULTILINE)
                        if ssid_match:
                            current_network = ssid_match.group(1)
                            print(f"Current Wi-Fi network: {current_network}")
                        else:
                            print("Wi-Fi is available but not connected to any network.")
                    else:
                        print("Wi-Fi utility not found. Your Mac might be using a different network management system.")
                except subprocess.CalledProcessError as e:
                    print(f"Error using airport command: {e}")
            
            print("\nNote: On macOS, retrieving Wi-Fi passwords requires admin privileges and")
            print("cannot be done directly through this script. You can use Keychain Access")
            print("application to view saved Wi-Fi passwords.")
            
        except Exception as e:
            print(f"Error retrieving Wi-Fi information: {e}")
            print("\nTry running the following commands manually in Terminal:")
            print("1. networksetup -listallhardwareports")
            print("2. /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I")
    
    elif system == "Linux":
        try:
            # Get list of connections
            print("Saved Wi-Fi networks:")
            networks = subprocess.check_output(
                ['nmcli', '-t', '-f', 'NAME,UUID', 'connection', 'show'], encoding='utf-8'
            ).splitlines()
            
            for network in networks:
                if ':' in network:  # Ensure it's a valid connection entry
                    name = network.split(':')[0]
                    print(f"Profile: {name:<30} | Password: [Requires sudo privileges]")
            
            print("\nNote: On Linux, retrieving Wi-Fi passwords requires sudo privileges.")
            print("You can use 'sudo nmcli connection show <name> | grep psk' to view passwords.")
            
        except subprocess.CalledProcessError as e:
            print(f"Error retrieving Wi-Fi information: {e}")
        except FileNotFoundError:
            print("Network Manager (nmcli) not found. This script requires Network Manager on Linux.")
    
    else:
        print(f"Unsupported operating system: {system}")

if __name__ == "__main__":
    get_wifi_profiles()