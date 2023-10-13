#!/bin/bash
# Based on: 
# https://openwrt.org/docs/guide-user/firewall/filtering_traffic_at_ip_addresses_by_dns

function print_help () {
	cat > $1 << EOF
Command syntax: 
$0 <table name> <chain type> <nft set name> <domain list>
	Add IP elements to NFT set to which domain names defined in domain list
	resolve to.

$0 --help | -h
	Print this help.
EOF
}

function print_msg_and_exit () {
	MSG_OUT=$([ $1 -eq 0 ] && echo "/dev/stdout" || \
				echo "/dev/stderr")

	if [ -n "$2" ]; then 
		echo $2 > $MSG_OUT
		echo "" > $MSG_OUT
	fi

	print_help $MSG_OUT

	exit $1
}


[ -n "$DEBUG" ] && [[ $(echo "$DEBUG" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
	set -xe || \
	set -e

[ -n "$PRETEND" ] && [[ $(echo "$PRETEND" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
	NFT="echo nft(pretend) " || \
	NFT="nft"


if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then 
	print_msg_and_exit 0
fi

if [ $# -ne 4 ]; then 
	print_msg_and_exit 1 "Incorrect syntax"
fi

# Set names must be 16 characters or less
TABLE_NAME=$1
CHAIN_TYPE=$2
SET_NAME=$3
DOMAIN_LIST=$4

if ! [[ "$TABLE_NAME" =~ ^([a-zA-Z0-9]){1,16}$ ]]; then
	print_msg_and_exit 3 "Provide correct table name"
fi

if ! [[ "$CHAIN_TYPE" =~ ^(filter|route|nat)$ ]]; then
	print_msg_and_exit 3 "Provide chain type"
fi

if ! [[ "$SET_NAME" =~ ^([a-zA-Z0-9]){1,16}$ ]]; then 
	print_msg_and_exit 3 "NFT set's name should be an alpha-numeric label of upto 16 char. long"
fi

if ! [ -f "$DOMAIN_LIST" ]; then 
	print_msg_and_exit 3 "Provide domainname source list"
fi

while read line; do 
	if [ -z "$line" ] || [ $(echo "$line" | cut -c -1) == "#" ]; then 
		# skip empty line, and comments line
		continue;
	fi

	if ! [[ "$line" =~ ^[a-zA-Z0-9|\-]{1,255}(\.[a-zA-Z0-9|\-]{1,255})*$ ]]; then
		echo "Ignorring '$line', not valid domain name"
		continue;
	fi

	DNAME=$line

	for ipaddr in $(curl --silent -H "accept: application/dns-json" \
		"https://1.1.1.1/dns-query?name=$DNAME&type=A" | \
		jq -r -c '.Answer[] | select(.type == 1) | .data'); do
		$NFT add element $TABLE_NAME $CHAIN_TYPE $SET_NAME {$ipaddr}
		# add. options: timeout 25h 
	done

done < "$DOMAIN_LIST"

exit 0
