#!/bin/bash
# Based on: 
# https://openwrt.org/docs/guide-user/firewall/filtering_traffic_at_ip_addresses_by_dns

[ -n "$PRETEND" ] && [[ $(echo "$PRETEND" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
        NFT="echo nft(pretend) " || NFT="nft"

[ -n "$DEBUG" ] && [[ $(echo "$DEBUG" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
        set -xe || set -e


if [ -f /etc/conf.d/nft-helper ] ; then
        . /etc/conf.d/nft-helper
fi

if [[ ! "$IP_TIMEOUT" =~ ^([0-9]{1,3}[s|m|h|d]){1,4}$ ]] ; then
	IP_TIMEOUT="3d"
	echo "Setting default IP timeout to: $IP_TIMEOUT"
fi

TIMEOUT_FLAG="timeout $IP_TIMEOUT"


function print_help () {
	cat > $1 << EOF
Command syntax: 
$0 <init|update|discard> <IP/domain list>
	init - add IP elements to NFT set. If domain name is provided it will be resolved to an IP address
	update - update IP elements in NFT set

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


if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then 
	print_msg_and_exit 0
fi

# check no. of arguments
if [ $# -ne 2 ]; then
	print_msg_and_exit 1 "Incorrect syntax"
fi

# Set names must be 16 characters or less
_ADDR_FAMILY=
_TABLE_NAME=
_SET_NAME=

ENTRY_LIST=$2

function set_afamily() {
	if ! [[ "$1" =~ ^(ip|ip6|inet|arp|bridge|netdev)$ ]]; then
		print_msg_and_exit 3 "Provide address family name"
	fi

	_ADDR_FAMILY=$1
}

function set_tblname () {
	if ! [[ "$1" =~ ^([a-zA-Z0-9_\.]){1,16}$ ]]; then
		print_msg_and_exit 3 "Provide correct table name"
	fi

	_TABLE_NAME=$1
}

function set_setname () {
	if ! [[ "$1" =~ ^([a-zA-Z0-9]){1,16}$ ]]; then
		print_msg_and_exit 3 "NFT set's name should be an alpha-numeric label of upto 16 char. long"
	fi

	_SET_NAME=$1
}


if ! [ -f "$ENTRY_LIST" ]; then
	print_msg_and_exit 3 "Provide domain/IP source list"
fi

function instr () {

	case $1 in
		\@set)
			set_afamily $2
			set_tblname $3
			set_setname $4

			load_set
		;;

		*)
			echo "Unknown instruction '$1'"
	esac
}

function op_init () {
	$NFT add element $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME { "$1" "$_FLAG_ARG" }
}

function op_update () {
	echo $_NFT_SET_IPs | grep -q "\"$1\"" && \
		$NFT delete element $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME { "$1" } || \
		echo "New IP addr. (as it has not been found in a current '$_SET_NAME' set): $1"

	$NFT add element $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME { "$1" "$_FLAG_ARG" }
}

# preparations before loading data
OP=$1
function load_set () {
	case $OP in
	init|update)

		SET_TYPE=$(nft --json list set $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME | jq -r '.nftables[1].set.type')
		SET_FLAGS=$(nft --json list set $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME | jq -r '.nftables[1].set.flags')

		if [ $(echo $SET_FLAGS | jq 'index("interval")') != 'null' ] && [ $OP == "update" ] ; then
			echo "Updates for 'interval' sets not supported, doing nothing"
			exit 0
		fi

		# get set IP's if any
		ELEM_ARR="$(nft --json list set $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME | jq '.nftables[1].set.elem')"
		if [ "$(echo $ELEM_ARR | jq '. != null')" = "true" ] ; then
			# IP list can be an array or object
			NFT_SET_IPs=$(echo "$ELEM_ARR" | jq '.[]')

			if $(echo $NFT_SET_IPs | egrep -q "^\"") ; then
				_NFT_SET_IPs=$(echo $NFT_SET_IPs | tr '\n' ' ')
			else
				# it's an object
				_NFT_SET_IPs=$(echo $NFT_SET_IPs | jq '.elem["val"]' | tr '\n' ' ')
			fi
		fi

		# check if timeout flag is set
		if [ $(echo $SET_FLAGS | jq 'index("timeout")') != 'null' ] ; then
			_FLAG_ARG="$TIMEOUT_FLAG"
		else
			if [ $OP == 'update' ] ; then
				echo "No timeout defined for '$SET_NAME', skipping update"
				exit 0
			fi

			_FLAG_ARG=""
		fi
	;;
	*)
		print_msg_and_exit 1 "Invalid operation: "
	;;
	esac
}

# read conf. file
line_no=0
while read line; do 
	line_no=$(($line_no+1))

	# cut comment and trim line
	line=$(echo "$line" | sed 's/\#.*/ /' | xargs)
	if [ -z "$line" ] ; then
		# skip empty line
		continue;
	fi


	if [[ "$line" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(\/[0-9]{1,2})?$ ]] ; then
		# ipv4 matched
		ip4_list=$line
	elif [[ "$line" =~ ^(\:\:)?[0-9a-fA-F]{1,4}(\:\:?[0-9a-fA-F]{1,4}){0,7}(\:\:)?(\/[0-9]{1,2})?$ ]] && \
	     [[ "$line" =~ ^.*\:.*\:.*(\/[0-9]{1,2})?$ ]]; then
		# ipv6 matched
		ip6_list=$line
	elif [[ "$line" =~ ^[a-zA-Z0-9|\-]{1,255}(\.[a-zA-Z0-9|\-]{1,255})*$ ]] ; then
		DNAME=$line
		# query CloudFlare DOH: 

		if [ $SET_TYPE == 'ipv4_addr' -o $SET_TYPE == 'ether_addr' ] ; then
			dns_aresp=$(curl --silent -H "accept: application/dns-json" \
							"https://1.1.1.1/dns-query?name=$DNAME&type=A")
			ip4_list=$(echo $dns_aresp | jq -r -c ".Answer[] | select(.name == \"$DNAME\") | .data")
		fi

		if [ $SET_TYPE == 'ipv6_addr' -o $SET_TYPE == 'ether_addr' ] ; then
			dns_aaaaresp=$(curl --silent -H "accept: application/dns-json" \
							"https://1.1.1.1/dns-query?name=$DNAME&type=AAAA")

			ip6_list=$(echo $dns_aaaaresp | jq -r -c ".Answer[] | select(.name == \"$DNAME\") | .data")
		fi
	elif [[ "$line" =~ ^\@[a-zA-Z0-9].*$ ]] ; then
		# set global variables to refer to set
		instr $line

		echo "$OP nft set: $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME"
		echo "Flags: $_FLAG_ARG"
	else 
		# no domain nor IP mached, skip line
		echo "WARN: Skipping line no. $line_no - no valid IP nor domain name: $line"
	fi

	for ipaddr in $ip4_list $ip6_list; do
		op_$OP $ipaddr
	done

done < "$ENTRY_LIST"

exit 0
