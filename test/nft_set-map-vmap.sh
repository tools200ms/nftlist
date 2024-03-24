#!/usr/sbin/nft -f

flush ruleset

# define inet family table
add table inet test_tbl

# define input, output and nat chains
add chain inet test_tbl test_in  { type filter hook input priority 0; policy drop; }
add chain inet test_tbl test_out { type filter hook output priority 0; policy accept; }
add chain inet test_tbl test_nat { type nat hook prerouting priority 0; policy drop; }

# define set, map, vmap
add set inet test_tbl blackhole  { type ipv4_addr ; flags timeout, interval; }
add map inet test_tbl porttoip   { type inet_service: ipv4_addr; }
add map inet test_tbl ipbanunban { type ipv4_addr: verdict; }

# add set elements
add element inet test_tbl blackhole { 10.5.0.8 }
add element inet test_tbl blackhole { 10.5.0.9 }

# add map  elements
add element inet test_tbl porttoip { 80: 10.11.0.142 }
add element inet test_tbl porttoip { 8080: 10.11.0.156 }

# add vmap  elements
add element inet test_tbl ipbanunban { 10.7.0.170: accept }
add element inet test_tbl ipbanunban { 10.7.0.171: drop }


# Rules:
add rule inet test_tbl test_in ip saddr @blackhole drop
add rule inet test_tbl test_nat dnat ip to tcp dport map @porttoip
add rule inet test_tbl test_out ip saddr @ipbanunban

