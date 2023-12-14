# NFT Helper - filter traffic by domain names
NFT Helper scripts has been developed to add domain name filtering capabilities to NFT firewall.
Desired domain names are read from configuration file, names are resolved to IP's that is used to
update NFT - thus to limit traffic to a limited domain set.

It's not a perfect filtering as different domain names share common IP's. Encrypted connections make not possible for firewall to validate destination domain. Therefore some extra names can 'sneak' under the radar. However taking into account how huge internet is this issue is absolutely negligible.

NFT Helper is useful with containerization/virtualisation technics where running VMs can be limited to exact resources they need.

NFT Helper is a set of scripts developed for Alpine Linux:
`/etc/init.d/nft-helper` - OpenRC script to ba launched in 'default' runlevel
`/etc/periodic/daily/nft-helper.daily.sh` - Script to be launched daily to refresh IP list
`/etc/nftsets/` - directory holding configuration
`/usr/local/bin/nft-helper.sh` - main script that does domain name resolution and sets NFT

---
**NOTE 1: **
Domain names are resolved using CloudFlares 1.1.1.1 DOH (DNS over HTTP(s)) server. This is actually the most secure way to query domain names.
---

---
**NOTE 2: **
`A` or `AAAA` records can change over time, therefore firewall shall be updated periodically. This is the role for the script `/etc/periodic/daily/nft-helper.daily.sh`.
---

## Configuration
IP addresses are grouped within 'NFT sets', sets are defined as part of table chain configuration.
To use `NFT Helper` define set such as:

```
table inet filter {
       set crepo4http {
               type ipv4_addr ;
               flags timeout ;
       }
}
```
IP address elements will be added by `NFT Helper`. There must be however protocol type defined: `ipv4_addr` or `ipv6_addr` and `timeout` flag added.
This snippet can be defined in `/etc/nftables.nft` or drop in `/etc/nftables.d/`.

`/etc/nftsets/` holds files with a list of domain names, the file name must follow specific name schema:
\<table name>-<chain type>-<set name>.list
For instance:
\/etc/nftsets/inet-filter-crepo4http.list


The content of the file might be: 
```
# Devuan repository for continer upodates

deb.devuan.org
deb.debian.org
```

Comments starting with \# can be used, also, you can mix domain names and IPv4 or IPv6 address, e.g.:
>\# Devuan repository for continer upodates
>deb.devuan.org  
>deb.debian.org
> \# IP address will be passed straight to NFT
>146.75.118.132

Finally add 'NFT Helper' to OpenRC:
```
rc-update add /etc/init.d/nft-helper default
```
## Running

`service nft-helper start` reads the configuration and launches `nft-helper.sh` to update NFT ruleset.

## Testing
You can see what NFT commands /root/bin/nft-update-sets.sh would do by setting `PRETEND` variable to 'yes'
```
PRETEND=yes nft-helper.sh tablef filter testset /etc/nftsets/tablef-filter-testset.list
```
Changes can be verified with:
```
# Reset firewall
service nftables restart

# checkout defined rules
nft list ruleset

# start NFT Helper:
service nft-helper start

# and verify what has been changed:
nft list ruleset
```

Enjoy!
