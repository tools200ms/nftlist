#!/bin/bash

nft flush ruleset

# add filter chain to ip table 'test.tbl'
nft add table ip test_tbl

# add OUTPUT hook
nft add chain test_tbl test_out { type filter hook output priority 0 \; }

nft add set ip test_tbl testset { type ipv4_addr \; flags timeout,interval \; }

# add counter
nft add rule ip test_tbl test_out ip daddr @testset counter


nft list ruleset

exit 0
