
from typing import Final

class About:
    name: Final = "NFT List"
    description: Final = "nftlist - network resource list loading and managing program."
    version: Final = "0.0.1"
    authors: Final = "Mateusz Piwek"
    command: Final = "nftlist"

    @staticmethod
    def getHelpMsg() -> str:
        text = f"Command syntax: \n\
        {About.command} <refresh|clean|panic> [--config_file|-c <path>] [--do_pretend|-d] [--verbose|-V] [--debug|-D]\n\
\n\
	refresh,r - Refresh Nftables sets according to settings in configuration.\n\
	clean,c   - Remove all elements loaded to Nftables sets referred in configuration.\n\
	panic,p,! - keep, or discard NFT sets that has been marked by directive @onpanic, \n\
                or determinated as\n\
\n\
	Optional: \n\
	--config_file|-c <path> - path to INI configuration file\n\
    --do_pretend|-d         - don't do any Nftables modifications, just display what would be done.\n\
    --verbose|-V            - add detailed messages\n\
    --debug|-D              - add debug messages\n\
    --quiet|-Q              - don't log any messages\n\
\n\
{About.command} --help | -h\n\
	Print this help\n\
\n\
{About.command} --version | -v\n\
	Print version\n\
        "

        return text

    @staticmethod
    def getVersionMsg() -> str:
        text = f"{About.name}, version: {About.version}\n    by: {About.authors}"

        return text

