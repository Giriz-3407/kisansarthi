import serial
import serial.tools.list_ports
import requests
import json
import time
import sys

BACKEND_URL = "http://127.0.0.1:5000/api/v1/ingest/soil-readings"
DEVICE_KEY = "device-key-esp32-01"
BAUD_RATE = 115200

def find_esp32_port():
    """Auto-detects the ESP32 COM port on Windows."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = port.description.lower()
        # Look for common USB-to-UART chips (CH9102, CP210x, CH340, etc.)
        if any(chip in desc for chip in ["ch9102", "cp210", "ch340", "ch341", "ftdi", "usb-serial", "uart"]):
            return port.device
    if ports:
        # Default to first available COM port
        return ports[0].device
    return None

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_esp32_port()
    if not port:
        print("[!] No USB COM port found. Please connect your ESP32 via USB cable.")
        print("[!] Available ports: ", [p.device for p in serial.tools.list_ports.comports()])
        sys.exit(1)

    print(f"[*] Found ESP32 on port {port}")
    print(f"[*] Opening serial connection at {BAUD_RATE} baud...")
    
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for ESP32 serial reset
        print(f"[+] Connected to {port} successfully!")
        print(f"[*] Forwarding sensor readings to: {BACKEND_URL}")
        print("[*] Press Ctrl+C to stop.\n" + "-" * 60)
    except Exception as e:
        print(f"[!] Could not open port {port}: {e}")
        print("[!] Tip: Close the Arduino IDE Serial Monitor if it is currently open.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "X-Device-Key": DEVICE_KEY
    }

    while True:
        try:
            raw_line = ser.readline()
            if not raw_line:
                continue

            line = raw_line.decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            # Check if this line is a JSON payload
            if line.startswith("{") and line.endswith("}"):
                try:
                    payload = json.loads(line)

                    # Ensure timestamp exists (use current UTC time if omitted)
                    if "timestamp" not in payload or not payload["timestamp"]:
                        payload["timestamp"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

                    print(f"[USB Read] {payload}")

                    resp = requests.post(BACKEND_URL, json=payload, headers=headers, timeout=5)
                    print(f"  --> Backend Ingest Response: [{resp.status_code}] {resp.text}\n")
                except json.JSONDecodeError:
                    print(f"[Serial] {line}")
                except requests.RequestException as e:
                    print(f"[!] Could not reach backend: {e}")
                    print("    Ensure Flask is running (py app.py)\n")
            else:
                # Regular debug or informational print from ESP32
                print(f"[ESP32 Debug] {line}")

        except KeyboardInterrupt:
            print("\n[*] Stopping serial bridge.")
            break
        except Exception as e:
            print(f"[!] Bridge error: {e}")
            time.sleep(1)

    ser.close()

if __name__ == '__main__':
    main()
