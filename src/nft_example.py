from nftables import Nftables
import json

from pprint import pprint

nft = Nftables()
nft.set_json_output(True)

rc, output, error = nft.cmd(
    "flush ruleset")

rc, output, error = nft.cmd(
    "add table inet test_tbl")

# Named set
rc, output, error = nft.cmd(
    "add set inet test_tbl blackhole " \
    "{ type ipv4_addr; }")

rc, output, error = nft.cmd(
    "add element inet test_tbl blackhole { 10.5.0.8, 10.5.0.9 }")

# Named map
rc, output, error = nft.cmd(
    "add map inet test_tbl porttoip " \
    "{ type inet_service: ipv4_addr; }")

rc, output, error = nft.cmd(
    "add element inet test_tbl porttoip { 80 : 10.11.0.142, 8080 : 10.11.0.156 }")

# Verdict Map
rc, output, error = nft.cmd(
    "add map inet test_tbl ipbanunban " \
    "{ type ipv4_addr: verdict; }")

rc, output, error = nft.cmd(
    "add element inet test_tbl ipbanunban { 192.168.1.200: accept, 192.168.1.201: drop }")

# Chains definition:
rc, output, error = nft.cmd(
    "add chain inet test_tbl test_in " \
    "{ type filter hook input priority 0; policy drop; }")

rc, output, error = nft.cmd(
    "add chain inet test_tbl test_out " \
    "{ type filter hook output priority 0; policy accept; }")

rc, output, error = nft.cmd(
    "add chain inet test_tbl test_nat " \
    "{ type nat hook prerouting priority 0; policy drop; }")

# Add rule referring to Set
rc, output, error = nft.cmd(
    "add rule inet test_tbl test_in ip saddr @blackhole drop")

# add rule referring to Map
rc, output, error = nft.cmd(
    "add rule inet test_tbl test_nat dnat ip to tcp dport map @porttoip")

# add rule referring to VMap
rc, output, error = nft.cmd(
    "add rule inet test_tbl test_out ip saddr @ipbanunban")

# Print ruleset:
rc, output, error = nft.cmd(
    "list ruleset")
pprint( json.loads(output) )

