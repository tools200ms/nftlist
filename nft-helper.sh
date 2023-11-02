#!/bin/bash
# Based on: 
# https://openwrt.org/docs/guide-user/firewall/filtering_traffic_at_ip_addresses_by_dns

DEFAULT_TIMEOUT="timeout 25h"

function print_help () {
	cat > $1 << EOF
Command syntax: 
$0 <init|update|discard> <table name> <chain type> <nft set name> <IP/domain list>
	init - add IP elements to NFT set. If domain name is provided it will be resolved to an IP address.
	update - update IP elements in NFT set, it works only for sets with type 'timeout' flag.

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

# check no. of arguments
if [ $# -ne 5 ]; then
	print_msg_and_exit 1 "Incorrect syntax"
fi

# Set names must be 16 characters or less
TABLE_NAME=$2
CHAIN_TYPE=$3
SET_NAME=$4
ENTRY_LIST=$5

if ! [[ "$TABLE_NAME" =~ ^([a-zA-Z0-9]){1,16}$ ]]; then
	print_msg_and_exit 3 "Provide correct table name"
fi

if ! [[ "$CHAIN_TYPE" =~ ^(filter|route|nat)$ ]]; then
	print_msg_and_exit 3 "Provide chain type"
fi

if ! [[ "$SET_NAME" =~ ^([a-zA-Z0-9]){1,16}$ ]]; then 
	print_msg_and_exit 3 "NFT set's name should be an alpha-numeric label of upto 16 char. long"
fi

if ! [ -f "$ENTRY_LIST" ]; then
	print_msg_and_exit 3 "Provide domain/IP source list"
fi

function op_init () {
	$NFT add element $TABLE_NAME $CHAIN_TYPE $SET_NAME { $1 $TIMEOUT }
}

function op_update () {
	echo $NFT_SET_IPs | grep -q "\"$1\"" && \
		$NFT delete element $TABLE_NAME $CHAIN_TYPE $SET_NAME { "$1" } || \
		echo "New IP addr. (as it has not been found in a current '$SET_NAME' set): $1"

	$NFT add element $TABLE_NAME $CHAIN_TYPE $SET_NAME { "$1" $TIMEOUT }
}

OP=$1
case $OP in
	init|update)
		# get set IP's if any
		ELEM_ARR="$(nft --json list set $TABLE_NAME $CHAIN_TYPE $SET_NAME | jq '.nftables[1].set.elem')"
		if [ "$(echo $ELEM_ARR | jq '. != null')" = "true" ] ; then
			# IP list can be an array or object
			NFT_SET_IPs=$(echo "$ELEM_ARR" | jq '.[]')

			if $(echo $NFT_SET_IPs | egrep -q "^\"") ; then
				NFT_SET_IPs=$(echo $NFT_SET_IPs | tr '\n' ' ')
			else
				# it's an object
				NFT_SET_IPs=$(echo $NFT_SET_IPs | jq '.elem["val"]' | tr '\n' ' ')
			fi
		fi

		# check if timeout flag is set
		if $(nft --json list set $TABLE_NAME $CHAIN_TYPE $SET_NAME | \
				jq '.nftables[1].set.flags' | grep -q "\"timeout\"") ; then

			TIMEOUT="$DEFAULT_TIMEOUT"
		else
			if [ $OP == 'update' ] ; then
				echo "No timeout defined for '$SET_NAME', skipping update"
				exit 0
			fi

			TIMEOUT=""
		fi
	;;
	*)
		print_msg_and_exit 1 "Invalid operation: "
	;;
esac


line_no=0

while read line; do 
	line_no=$(($line_no+1))
	if [ -z "$line" ] || [ $(echo "$line" | cut -c -1) == "#" ]; then 
		# skip empty line, and comments line
		continue;
	fi

	if [[ "$line" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]] ; then
		# ipv4 matched
		ip_list=$line
	elif [[ "$line" =~ ^(\:\:)?[0-9a-fA-F]{1,4}(\:\:?[0-9a-fA-F]{1,4}){0,7}(\:\:)?$ ]] && \
	     [[ "$line" =~ ^.*\:.*\:.*$ ]]; then
		# ipv6 matched
		ip_list=$line
	elif [[ "$line" =~ ^[a-zA-Z0-9|\-]{1,255}(\.[a-zA-Z0-9|\-]{1,255})*$ ]]; then
		DNAME=$line
		# query CloudFlare DOH: 
		dns_resp=$(curl --silent -H "accept: application/dns-json" \
				"https://1.1.1.1/dns-query?name=$DNAME&type=A")

		ip_list=$(echo $dns_resp | jq -r -c '.Answer[] | select(.type == 1) | .data')
	else 
		# no domain nor IP mached, skip line
		echo "WARN: Skipping line no. $line_no - no valid IP nor domain name: $line"
	fi

	for ipaddr in $ip_list; do
		op_$OP $ipaddr
	done

done < "$ENTRY_LIST"

exit 0
