import nmap
import time

network = "your pi IP"   # ← change this if needed

scanner = nmap.PortScanner()

print("Scanning network:", network)
print("-" * 40)

scanner.scan(hosts=network, arguments='-sn')

for host in scanner.all_hosts():
    if 'mac' in scanner[host]['addresses']:
        mac = scanner[host]['addresses']['mac']
    else:
        mac = "No MAC Found"

    print(f"IP: {host}")
    print(f"MAC: {mac}")
    print(f"STATUS: {scanner[host].state()}")
    print("-" * 40)
