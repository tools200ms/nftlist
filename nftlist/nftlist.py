
from nftables import Nftables
import json

from pprint import pprint

command="nftlist"

print(f"Command syntax: \
{command} <update|purge|panic> [--all]|[--set <address family> <table> <set>] [--configpath] [--includedir <path>] \
\
c	update,u - updates NFT sets according to settings from configuration\
	clean,c   - delete all elements of NFT sets referred in configuration\
	panic,p,! - keep, or discard NFT sets that has been marked by directive @onpanic\
\
	Optional:\
	<conf path> - path to file or directory configuration, if path is a directory\
	              all '*.list' files under this location are loaded (no recurcive search)\
\
	--set,-s - define set, replaces '@set' directive from file\
	--includedir,-D - indicates search directory for files included with '@include' directive\
\
	If settings are not provided, default values are:\
		'$_DEFAULT_CONF' as configuration directory and\
		'$_DEFAULT_INCL' as include directory is used\
\
$(basename $0) --help | -h\
	Print this help\
\
$(basename $0) --version | -v\
	Print version")

exit(0)
