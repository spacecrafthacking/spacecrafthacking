import socket
import sys

MODEM_IP = "127.0.0.1"      # IP of the OpenWrt modem
MODEM_PORT = 9000
FIRMWARE_URL = "http://10.0.0.1:8080/firmware.bin"  # served from your ground container

def main():
    url = FIRMWARE_URL
    if len(sys.argv) > 1:
        url = sys.argv[1]

    cmd = f"UPDATE {url}\n"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((MODEM_IP, MODEM_PORT))
    s.sendall(cmd.encode("ascii"))

    # Read responses until socket closes
    while True:
        data = s.recv(4096)
        if not data:
            break
        sys.stdout.write(data.decode("ascii", errors="replace"))
        sys.stdout.flush()

    s.close()

if __name__ == "__main__":
    main()

