import ipaddress
import argparse
import sys


def print_help():
    """
    Prints help information for using the program.
    """
    help_text = """
    IP Address Splitter
    -------------------
    This program reads a file containing IP addresses (one per line) 
    and splits them into two files: one for IPv4 and one for IPv6.

    Usage:
        python ip_splitter.py -i <input_file> -4 <ipv4_file> -6 <ipv6_file>

    Arguments:
        -i, --input   Path to the input file containing IP addresses.
        -4, --ipv4    Path to the output file for IPv4 addresses.
        -6, --ipv6    Path to the output file for IPv6 addresses.
        -h, --help    Display this help message.

    Example:
        python ip_splitter.py -i input_ips.txt -4 ipv4_only.txt -6 ipv6_only.txt
    """
    print(help_text)


def split_ip_addresses(input_file, ipv4_file, ipv6_file):
    """
    Reads a file with IP addresses, separates IPv4 and IPv6 addresses,
    and writes them to separate files.

    :param input_file: Path to the input file containing IP addresses.
    :param ipv4_file: Path to the output file for IPv4 addresses.
    :param ipv6_file: Path to the output file for IPv6 addresses.
    """
    try:
        with open(input_file, 'r') as infile, \
                open(ipv4_file, 'w') as ipv4_out, \
                open(ipv6_file, 'w') as ipv6_out:

            for line in infile:
                address = line.strip()
                if not address:
                    continue  # Skip empty lines

                try:
                    ip = ipaddress.ip_address(address)
                    if isinstance(ip, ipaddress.IPv4Address):
                        ipv4_out.write(f"{address}\n")
                    elif isinstance(ip, ipaddress.IPv6Address):
                        ipv6_out.write(f"{address}\n")
                except ValueError:
                    print(f"Invalid IP address: {address}", file=sys.stderr)  # Log invalid entries
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Split a file of IP addresses into separate IPv4 and IPv6 files.",
        add_help=False
    )
    parser.add_argument('-i', '--input', required=True, help="Input file with a list of IP addresses.")
    parser.add_argument('-4', '--ipv4', required=True, help="Output file for IPv4 addresses.")
    parser.add_argument('-6', '--ipv6', required=True, help="Output file for IPv6 addresses.")
    parser.add_argument('-h', '--help', action='store_true', help="Display help message.")

    args = parser.parse_args()

    if args.help:
        print_help()
        sys.exit(0)

    split_ip_addresses(args.input, args.ipv4, args.ipv6)


if __name__ == "__main__":
    main()
