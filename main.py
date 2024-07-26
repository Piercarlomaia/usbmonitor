import os
import sys
import logging
import subprocess
import time
import pandas as pd

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def is_windows():
    return os.name == 'nt'


def get_usb_devices_windows():
    try:
        result = subprocess.run(['powershell', '-Command',
                                 'Get-PnpDevice -PresentOnly'],
                                capture_output=True, text=True, check=True)
        devices = result.stdout.strip().split('\n')
        return devices
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to execute PowerShell command: {e}")
        return []


def get_usb_devices_linux():
    try:
        result = subprocess.run(['lsusb'],
                                capture_output=True, text=True, check=True)
        devices = result.stdout.strip().split('\n')
        return devices
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to execute lsusb command: {e}")
        return []


def parse_devices(devices):
    if is_windows():
        header = devices[0].split()
        parsed_devices = [dict(zip(header, device.split())) for device in devices[2:] if device.strip()]
    else:
        parsed_devices = [{"Device": device} for device in devices if device.strip()]
    return parsed_devices


def compare_device_lists(old_list, new_list):
    old_set = set(tuple(device.items()) for device in old_list)
    new_set = set(tuple(device.items()) for device in new_list)

    added_devices = [dict(device) for device in (new_set - old_set)]
    removed_devices = [dict(device) for device in (old_set - new_set)]

    return added_devices, removed_devices


def print_devices(devices):
    df = pd.DataFrame(devices)
    logging.debug(f"\n{df.to_string(index=False)}")


def monitor_usb_changes_windows():
    logging.info("Starting USB device monitoring on Windows...")

    previous_devices = parse_devices(get_usb_devices_windows())
    #logging.debug("Initial devices:")
    #print_devices(previous_devices)

    while True:
        time.sleep(5)  # Polling interval

        current_devices = parse_devices(get_usb_devices_windows())
        #logging.debug("Current devices:")
        #print_devices(current_devices)

        added_devices, removed_devices = compare_device_lists(previous_devices, current_devices)

        if added_devices:
            logging.info("Devices connected:")
            print_devices(added_devices)

        if removed_devices:
            logging.info("Devices disconnected:")
            print_devices(removed_devices)

        previous_devices = current_devices


def monitor_usb_changes_linux():
    logging.info("Starting USB device monitoring on Linux...")

    previous_devices = parse_devices(get_usb_devices_linux())
    logging.debug("Initial devices:")
    print_devices(previous_devices)

    while True:
        time.sleep(5)  # Polling interval

        current_devices = parse_devices(get_usb_devices_linux())
        logging.debug("Current devices:")
        print_devices(current_devices)

        added_devices, removed_devices = compare_device_lists(previous_devices, current_devices)

        if added_devices:
            logging.info("Devices connected:")
            print_devices(added_devices)

        if removed_devices:
            logging.info("Devices disconnected:")
            print_devices(removed_devices)

        previous_devices = current_devices


def main():
    if is_windows():
        monitor_usb_changes_windows()
    else:
        monitor_usb_changes_linux()


if __name__ == '__main__':
    main()
