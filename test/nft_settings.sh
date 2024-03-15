#!/bin/bash

nft flush ruleset

# add filter chain to ip table 'test.tbl'
nft add table inet test_tbl

# add OUTPUT hook
nft add chain inet test_tbl test_out { type filter hook output priority 0 \; }

nft add set inet test_tbl testset1d { type ipv6_addr \; flags timeout \; }
nft add set inet test_tbl testset2s { type ipv4_addr \; flags interval \; }

# add counter
nft add rule inet test_tbl test_out ip6 daddr @testset1d counter
nft add rule inet test_tbl test_out ip saddr @testset2s counter

nft list ruleset


exit 0
