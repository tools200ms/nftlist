#!/usr/sbin/nft -f

flush ruleset

# add filter chain to ip table 'test.tbl'
add table inet test_tbl

# add OUTPUT hook
add chain inet test_tbl test_out { type filter hook output priority 0 ; }
add chain inet test_tbl test_in  { type filter hook input priority 0 ; }

add set inet test_tbl testset1d { type ipv6_addr ; flags timeout ; }
add set inet test_tbl testset2s { type ipv4_addr ; flags timeout, interval ; auto-merge ; }

add set inet test_tbl blacklist { type ipv4_addr ; flags timeout, interval ; auto-merge ; }

# add counter
add rule inet test_tbl test_out ip6 daddr @testset1d counter
add rule inet test_tbl test_out ip saddr @testset2s counter

list ruleset
