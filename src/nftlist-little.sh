#!/bin/bash
# Based on: 
# https://openwrt.org/docs/guide-user/firewall/filtering_traffic_at_ip_addresses_by_dns

_VERSION="1.2.9-alpha" # --PKG_VERSION_MARK-- DO NOT REMOVE THIS COMMENT

[ -n "$PRETEND" ] && [[ $(echo "$PRETEND" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
        NFT="echo nft(pretend) " || NFT="nft"

[ -n "$DEBUG" ] && [[ $(echo "$DEBUG" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
        set -xe || set -e


function print_version () {
	echo 'NFT List little, version: '$_VERSION
	echo "Created by Mateusz Piwek, released with MIT License"
}

_DEFAULT_EL_TIMEOUT="3d"
_DEFAULT_CONF='/etc/nftlists/enabled'
_DEFAULT_INCL='/etc/nftlists/included'


function print_help () {
	cat > $1 << EOF
Command syntax: 
$(basename $0) <update|purge|panic> [conf. path] [--set <address family> <table> <set>] [--includedir <path>]

	update,u - updates NFT sets according to settings from configuration
	purge    - delete all elements of NFT sets referred in configuration
	panic    - keep, or discard NFT sets that has been marked by directive @onpanic

	Optional:
	<conf path> - path to file or directory configuration, if path is a directory
	              all '*.list' files under this location are loaded (no recurcive search)

	--set,-s - define set, replaces '@set' directive from file
	--includedir,-D - indicates search directory for files included with '@include' directive

	If settings are not provided, default values are:
		'$_DEFAULT_CONF' as configuration directory and
		'$_DEFAULT_INCL' as include directory is used

$(basename $0) --help | -h
	Print this help

$(basename $0) --version | -v
	Print version

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

if [ "$1" == "-v" ] || [ "$1" == "--version" ]; then
	print_version
	exit 0
fi

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then 
	print_msg_and_exit 0
fi

if [ "$1" == "init" ]; then
  mkdir -p /etc/nftlists/available /etc/nftlists/enabled /etc/nftlists/included
fi

# check no. of arguments
if [ $# -lt 2 ] && [ $# -gt 4 ] ; then
	print_msg_and_exit 1 "ArgErr: Incorrect syntax"
fi

# global variables:
_ADDR_FAMILY=
_TABLE_NAME=
_SET_NAME=

_SET_TYPE=
_NFT_SET_IPs=

# BEGIN: validating function
function set_afamily() {
	if [ "$1" == '-' ]; then
		if [ -z "$_ADDR_FAMILY" ] ; then
			print_msg_and_exit 3 "ConfigErr: Address family has not been defined before, can not apply copy '-' sign"
		fi

		return;
	fi

	if ! [[ "$1" =~ ^(ip|ip6|inet|arp|bridge|netdev)$ ]]; then
		print_msg_and_exit 3 "ConfigErr: Address family name has not been provided"
	fi

	_ADDR_FAMILY=$1
}

function set_tblname () {
	if [ "$1" == '-' ]; then
		if [ -z "$_TABLE_NAME" ] ; then
			print_msg_and_exit 3 "ConfigErr: Table name has not been defined before, can not apply copy '-' sign"
		fi

		return;
	fi

	if ! [[ "$1" =~ ^([a-zA-Z0-9_\.]){1,16}$ ]]; then
		print_msg_and_exit 3 "ConfigErr: Provide correct table name"
	fi

	_TABLE_NAME=$1
}

function set_setname () {
	if [ "$1" == '-' ]; then
		if [ -z "$_SET_NAME" ] ; then
			print_msg_and_exit 3 "ConfigErr: Set name has not been defined before, can not apply copy '-' sign"
		fi

		return;
	fi

	# Set names must be 16 characters or less
	if ! [[ "$1" =~ ^([a-zA-Z0-9]){1,64}$ ]]; then
		print_msg_and_exit 3 "ConfigErr: NFT set's name should be an alpha-numeric label of upto 16 char. long"
	fi

	_SET_NAME=$1
}
# END

# BEGIN: read file or directory path
if [ -z "$2" ] ; then
	# default configuration location
	LIST_INPUT=$_DEFAULT_CONF
	INC_LIST_INPUT=$_DEFAULT_INCL
else
	LIST_INPUT=$2
	INC_LIST_INPUT=
fi

if [ ! -e "$LIST_INPUT" ] ; then
	echo "Location does not exists: '$LIST_INPUT'"
	exit 3
fi


LIST_INPUT=$(realpath "$LIST_INPUT")

if [ -d "$LIST_INPUT" ] ; then
	_files_list=$(find -L "$LIST_INPUT" -maxdepth 1 -type f -name '*.list' | sort)
  if [ -z "$_files_list" ] ; then
    echo "Conf. directory exists, but no conf. files found."
    exit 0
  fi
elif [ -f "$LIST_INPUT" ] ; then
	_files_list=("$LIST_INPUT")
else
  echo "'path' should be a file or directory"
  exit 4
fi

# END

# BEGIN load configuration:
if [ -f /etc/conf.d/nftlist ] ; then
        . /etc/conf.d/nftlist
fi

if [[ "$TIMEOUT" =~ ^([0-9]{1,3}[s|m|h|d]){1,4}$ ]] ; then
  # overwrite default elem. timeout.
	_DEFAULT_EL_TIMEOUT=$TIMEOUT
fi
# END


function load_directive () {
	case $1 in
		\@set)
			set_afamily $2
			set_tblname $3
			set_setname $4

			read_set
			echo "$_FLAG_ARG"
		;;

		\@include)
			# Before calling this script recursively check if:
			# 1. included file is not the same as the one that is under
			#    process
			# 2. if there is no 'parent' process that has
			# as an argument the same file.
			#
			# This is to avoid circular calls.

			if [ -z "$2" ]; then
				print_msg_and_exit 5 "ConfErr: Syntax error, missing parameter for '@include'"
			fi

			local incl_file="$(dirname $2)/$(basename $2)"

			if  [ -z "$INC_LIST_INPUT" ]; then
				print_msg_and_exit 5 "ConfErr: Include path has not been set"
			fi

			if ! [ -e "$INC_LIST_INPUT/$incl_file" ]; then
				echo "DataErr: Can not find file that has been declared in @include: '$2'"
				# reset set an continue
				_ADDR_FAMILY=
				_TABLE_NAME=
				_SET_NAME=
			elif ! [ -f "$INC_LIST_INPUT/$incl_file" ]; then
				print_msg_and_exit 5 "ConfErr: Included file is not a regular file: '$INC_LIST_INPUT/$incl_file'"
			fi

			if [ -n "$_incl_file" ]; then
				print_msg_and_exit 5 "ConfErr: File can not be included from already included file: '$INC_LIST_INPUT/$incl_file' includes '$_incl_file'"
			fi

			_incl_file="$INC_LIST_INPUT/$incl_file"
		;;

		\@onpanic)
			echo 'keep' 'discard'
		;;

		*)
			echo "Unknown directive '$1'"
	esac
}

# BEGIN: function performing NFT operations:
function load_init () {
	$NFT add element $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME { "$1" "$_FLAG_ARG" }
}

function load_update () {
	echo $_NFT_SET_IPs | grep -q "\"$1\"" && \
		$NFT delete element $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME { "$1" } || \
		echo "New IP addr. (as it has not been found in a current '$_SET_NAME' set): $1"

	$NFT add element $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME { "$1" "$_FLAG_ARG" }
}
# END

# preparations before loading data

function read_set () {

	_SET_TYPE=$(nft --json list set $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME | jq -r '.nftables[1].set.type')
	local SET_FLAGS=$(nft --json list set $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME | jq -r '.nftables[1].set.flags')

	# get set IP's if any
	ELEM_ARR="$(nft --json list set $_ADDR_FAMILY $_TABLE_NAME $_SET_NAME | jq '.nftables[1].set.elem')"

	if [ "$(echo $ELEM_ARR | jq '. != null')" = "true" ] ; then
		# IP list can be an array or object
		local NFT_SET_IPs=$(echo "$ELEM_ARR" | jq '.[]')

		if $(echo $NFT_SET_IPs | egrep -q "^\"") ; then
			_NFT_SET_IPs=$(echo $NFT_SET_IPs | tr '\n' ' ')
		else
			# it's an object
			_NFT_SET_IPs=$(echo $NFT_SET_IPs | jq '.elem["val"]' | tr '\n' ' ')
		fi
	else
		_NFT_SET_IPs=
	fi

	_FLAG_ARG=
	# check if timeout flag is set
	if [ $(echo $SET_FLAGS | jq 'index("timeout")') != 'null' ] ; then
		_FLAG_ARG="timeout $_DEFAULT_EL_TIMEOUT"
	else
		_FLAG_ARG=""
	fi
}

# read conf. file
_line_no=0
_incl_line_no=0

function parse_line() {
	line=$1
	_line_no=$(($_line_no+1))

	# cut comment and trim line
	line=$(echo "$line" | sed 's/\#.*/ /' | xargs)
	if [ -z "$line" ] ; then
		# skip empty line
		return;
	fi

	if [[ "$line" =~ ^\@[a-zA-Z0-9].*$ ]] ; then
		# set global variables to refer to set
		echo -n "Loading $line: "
		load_directive $line

		return;
	fi

	if [ -z "$_SET_NAME" ]; then
		print_msg_and_exit 4 "ConfigErr: NFT set is not defined"
	fi

	local addr_list=''

	if [[ "$line" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(\/[0-9]{1,2})?$ ]] ; then
		# ipv4 matched
		addr_list=$line
	elif [[ "$line" =~ ^(\:\:)?[0-9a-fA-F]{1,4}(\:\:?[0-9a-fA-F]{1,4}){0,7}(\:\:)?(\/[0-9]{1,2})?$ ]] && \
	     [[ "$line" =~ ^.*\:.*\:.*(\/[0-9]{1,2})?$ ]]; then
		# ipv6 matched
		addr_list=$line
	elif [[ "$line" =~ ^([0-1a-fA-F][0-1a-fA-F]\:){5}[0-1a-fA-F][0-1a-fA-F]$ ]] ; then
		addr_list=$line
	elif [[ "$line" =~ ^[a-zA-Z0-9|\-]{1,255}(\.[a-zA-Z0-9|\-]{1,255})*$ ]] ; then
		# domain name matched
		DNAME=$line
		# query CloudFlare DOH: 

		case $_SET_TYPE in
			ipv4_addr)
				dns_resp=$(curl --silent --connect-timeout 3.14 -H "accept: application/dns-json" \
							"https://1.1.1.1/dns-query?name=$DNAME&type=A" || true)

				if [ -n "$dns_resp" ] && [ $(echo $dns_resp | jq -c ".Answer != null") == 'true' ] ; then
					addr_list=
					for resp in $(echo $dns_resp | jq -r -c ".Answer[] | select(.type == 1) | .data"); do
						if [ $resp == "0.0.0.0" ] || [ $resp == "127.0.0.1" ]; then
							echo "DataErr: illegal response for $DNAME: $resp"
							continue;
						fi

						addr_list="$addr_list $resp"
					done

					if [ -z "$addr_list" ]; then
						echo "DataErr: no responce data"
					fi
				else
					# No answer section for
					echo "DataErr: Can't resolve '$DNAME' A"
				fi
				;;

			ipv6_addr)
				dns_resp=$(curl --silent --connect-timeout 3.14 -H "accept: application/dns-json" \
							"https://1.1.1.1/dns-query?name=$DNAME&type=AAAA" || true)

				if [ -n "$dns_resp" ] && [ $(echo $dns_resp | jq -c ".Answer != null") == 'true' ] ; then
					addr_list=$(echo $dns_resp | jq -r -c ".Answer[] | select(.type == 28) | .data")

				else
					# No answer section for
					echo "DataErr: Can't resolve '$DNAME' AAAA"
				fi
				;;
			*)
				# wrong SET_TYPE for domain name resolution results, at this point SET_TYPE can not be empty (it has been set together with _SET_NAME)
				# domain name can be resolved only to type 'ipv4_addr' or 'ipv6_addr'
				# but other type has been set
				echo "DataErr: Can not add domain name IP - set '$_ADDR_FAMILY $_TABLE_NAME $_SET_NAME' is of an incorrect type"
				;;
		esac
	else 
		# no domain nor IP matched, skip line
		echo "DataErr: Skipping line no. $line_no - no valid IP nor domain name: $line"
	fi

	local load_fun=

	if [ -z "$_NFT_SET_IPs" ]; then
		load_fun='load_init'
	else
		load_fun='load_init'
	fi

	for addr in $addr_list; do
		$load_fun $addr
	done
}


for file in $_files_list ; do
	echo "Loading file: $file"

	while read line; do

		parse_line "$line"

		if [ -n "$_incl_file" ]; then
			# if file has been included via @include directive load content from that file

			echo "Loading file: $incl_file"
			while read incl_line; do
				parse_line "$incl_line"
			done < "$_incl_file"

			# release incl. file
			_incl_file=
		fi

	done < "$file"
done

exit 0
