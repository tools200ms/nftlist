#!/bin/bash

# Set interface name that corresponds to your system settings:
NIC="eth0"

# Flush existing rules and ipsets
iptables -F
iptables -X
ipset destroy

# Create ipsets for allowed hosts and ports
ipset create allowed_hosts hash:ip timeout 0
ipset create allowed_tcp_ports bitmap:port range 1-65535

# Populate ipsets
# Add allowed hosts
ipset add allowed_hosts 192.168.1.10
ipset add allowed_hosts 192.168.1.11
ipset add allowed_hosts 10.0.0.5

# Add allowed TCP ports
ipset add allowed_tcp_ports 22        # SSH
ipset add allowed_tcp_ports 80        # HTTP
ipset add allowed_tcp_ports 443       # HTTPS
ipset add allowed_tcp_ports 8080      # HTTP-alt
ipset add allowed_tcp_ports 3000-5000 # Port range example

# Set default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback traffic
iptables -A INPUT -i lo -j ACCEPT -m comment \
  --comment "Accept any localhost traffic"

# Drop invalid connections
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP -m comment \
  --comment "Drop invalid connections"

# Accept established and related traffic
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED \
  -j ACCEPT -m comment \
  --comment "Accept traffic originated from us"

# Allow connections from allowed_hosts to allowed_tcp_ports
iptables -A INPUT -i "$NIC" -p tcp -m set \
  --match-set allowed_hosts src -m set \
  --match-set allowed_tcp_ports dst \
  -m conntrack --ctstate NEW -j ACCEPT -m comment \
  --comment "Accept connections for chosen IPs to selected ports"
