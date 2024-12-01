from dnslib import DNSRecord, DNSHeader, QTYPE
import socket

def add_ip(ip, timeout):
    subprocess.run(["/path/to/add_ip", ip, timeout])

def resolve_and_log(query):
    # Forward query to an upstream server
    upstream = ('8.8.8.8', 53)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(query.pack(), upstream)
    response, _ = sock.recvfrom(512)
    resolved = DNSRecord.parse(response)
    for rr in resolved.rr:
        if QTYPE[rr.rtype] == "A":
            add_ip(rr.rdata, "timeout_value")
    return response

def start_dns_proxy():
    server = ('0.0.0.0', 53)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server)

    while True:
        query, addr = sock.recvfrom(512)
        response = resolve_and_log(DNSRecord.parse(query))
        sock.sendto(response, addr)

if __name__ == "__main__":
    start_dns_proxy()
