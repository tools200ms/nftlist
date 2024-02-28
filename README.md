# NFT Helper - filter traffic by domain names + split configuration
**NOTE 1:**
Usage of this tool requires knowledge regarding Linux NFT firewall framework.
To familiarize with NFT see [NFT Quick reference in 10 minutes](https://wiki.nftables.org/wiki-nftables/index.php/Quick_reference-nftables_in_10_minutes).
Also, descriptions of the topic with an examples can be found in [Useful links](#useful-links) section at the end of this page.


While managing a computer network security it is practical to limit or open network traffic basing on IP addresses resolved from
a given domain name list. Furthermore, it is practical and recommended to keep data (domain names, IPs) separated from structure (firewall configuration).


As domain-based filtering is not in a scope of Nftables tools, I developed this set of scripts to full fill this feature.
As a 'side effect', I could keep my settings outside of `.nft` config files, so after all `NFT Helper` is
complementing piece of software for Nftables.

1. Domain names are resolved by `NFT Helper` using CloudFlare `1.1.1.1` DOH (DNS over HTTP(s)) server. This is actually the most secure way to query domain names.
2. `NFT Helper` handles following network resources:
    * Domain names (example.com) and:
    * IPv4 addresses (10.0.23.3)
    * IPV4 networks (103.31.4.0/22)
    * IPv6 addresses (fe80::e65f:1ff:fe1b:5bee)
    * IPv6 networks (2001:db8:1234::/48)

    These data is read from [configuration files](#configuration) and loaded to appropriate [NFT set](#nft-sets).
3. IPs pointed by DNS can change over time, thus `NFT Helper` runs periodic checks to keep firewall coherent with internet state.

Please note that domain based filtering is not a perfect one. Usually multiple domain names share common IP's. Encrypted connections (that protect privacy) prevent firewall from inspecting network package for source/destination check. Therefore some extra names can 'sneak' under the radar. However this issue is negligible comparing to benefits coming from restricted firewall rule set.

# NFT sets



To summarise, you focus on constructing of a proper NFT configuration, while NFT Helper is a tool that is to fill defined NFT sets with desired IP resources.


# Configuration

`NFT Helper` loads configuration files by default from:
```
/etc/nftdef/
```
Configuration file mus end with:
```
.list
```
extension.

The format is one domain/IPv per line


To provide flexible configuration, following instructions has been introduced:

**\@set family|- \<table name\>|- \<set name\>|-**

this defines NFT set to be filled with certain IP/IP range elements

**\@include \<file name\>**
this allows on inclusion of a certain file


**\@onpanic keep|discard**
this allows to define if a certain list should be keeped, or removed in the case of 'panic' signal




# NFT sets

NFT configuration shall be defined in `/etc/nftables.nft` and in `/etc/nftables.d/`. NFT helper does not create, modify or delete any
hooks, chains, or other 'structural' firewall settings. It only operates within NFT sets, 'NFT helper' can only:
* add, or
* remove **elements** of an indicated NFT sets.

In short, in NFT, IP addresses are grouped within `NFT sets`, every IP or network address is defined as `set element`.
Sets are a part of a firewall table where appropriate accept/reject/drop polices can be defined.



# Package content

NFT Helper is a set of scripts originally developed to protect a small server run at Alpine Linux:
`/etc/init.d/nft-helper` - OpenRC script to be launched in 'default' runlevel
`/etc/periodic/daily/nft-helper.daily.sh` - script to be launched daily (preferably) to refresh IP list
`/usr/local/bin/nft-helper.sh` - finally, the main script that does domain name resolution and sets NFT

Configuration for NFT-helper that is a set of files holding the list of domain names is designed to be placed in
```
/etc/nftdef/
```
directory. The files should end with `*.list` extension to be loaded.


**NOTE 1:**



**NOTE 2:**
`A` or `AAAA` records can change over time, therefore firewall shall be updated periodically. This is the role for the script `/etc/periodic/daily/nft-helper.daily.sh`.


## Configuration


### 1. Define NFT set to be feed by NFT-helper
Define a set such as:

```
table inet filter {
       set repo4http {
               type ipv4_addr ;
               flags timeout ;
       }
}
```
This definition can be added to `/etc/nftables.nft`, or preferably dropped as a separate configuration file to `/etc/nftables.d/` directory.

To reload configuration do:
```bash
service nftables reload
```

**NOTE 4:**
Set specification `typeof` is not supported yet, please use `type` for any sets to be feed by 'nft-helper'.

NFT sets should be bound with an appropriate chain rules that implement black/white listing policy, for instance:
```
table inet filter {
        ...
        chain forward {
                type filter hook forward priority filter; policy drop;
                ...
                iifname $NIC_BR0 oifname $NIC_EXT ip daddr @repo4http tcp dport {http, https} counter accept
        }
        ...
}
```
Above snippet defines the rule that do `accept` only `http` and `https` traffic to IP destinations defined in `crepo4http` set.

### 2. Define resource list

Create in `/etc/nftdef/` file `<name>.list`, e.g. `access.list`.

The content of the file might be:
```
# Devuan repository access
@set inet filter repo4http

deb.devuan.org
deb.debian.org

@set inet filter ext4http
 # IP address will be passed straight to NFT
146.75.118.132 # special IP
```

`\#` indicates that a text afterwards is a comment.

You can mix domain names and IP address. Both, IPv4 and IPv6 are acknowledged by NFT-helper.

However, ensure that `type` specification of IP set matches provided address family, e.g. if `type ipv4_addr` is defined, adding IPv6 address to set will fail.
Depending on what type is defined, NFT-helper resolves:

* `A` DNS records for `type ipv4_addr`
* `AAAA` DNS records for `type ipv6_addr`
* `A` and `AAAA` DNS records for `ether_addr`

### 3. Feed NFT with data

To feed NFT set call `nft-helper.sh`:
```
nft-helper.sh init /etc/nftsets/access.list
```
This will query domain names encountered in `/etc/nftsets/access.list` and feed `repo4http` set with resolved IP's.
If `access.list` holds IP addresses, it will just validate and copy them to an IP set.

**NOTE 4:**
You can provide network addresses e.g. `103.22.200.0/22`. In this case NFT set must have specified `interval` flag. e.g.:
```
set setname {
        type ipv4_addr ;
        flags timeout,interval ;
}
```

Finally add 'NFT Helper' to OpenRC's default runlevel:
```
rc-update add /etc/init.d/nft-helper default
```

and bellow command:
```
service nft-helper start
```
will configure NFT sets according to configuration found in `/etc/nftdef/*.list` files.

### 4. NFT updates

There is a probability that some IP addresses might not be associated with a certain domain anymore.
While other new IP's might be added.

`nft-helper.sh` comes with `update` option and cron script for periodic IP checkouts. It is recommended to lookup for a domain name once per day to give a chance for a smooth firewall update.
In this case flag `timeout` shall be defined in NFT set.
If so, any IP's added to this set will be bound with 72 hour timeout. Periodic update will reset timeouts
back to 72 hours. But if one of the IP's is not resolved any more it will simply get expired. If there
are new IP's then NFT set will be complemented.

To have updates running ensure that `/etc/periodic/daily/nft-helper.daily.sh` is launched with no-errors.


## Testing
You can see what `nft-helper.sh` would do by setting `PRETEND` variable to 'yes'
```
PRETEND=yes nft-helper.sh init inet filter testset /etc/nftsets/inet-filter-testset.list
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

# Summary

NFT Helper is useful with containerization/virtualisation technics where running VMs can be limited to exact network resources they need. I developed it to have a lite, robust and straight-forward solution for various  NFT firewall cases.

# Useful links

HowTo:
* Nftables Wiki [here](https://wiki.nftables.org/)
* Gentoo Nftables guide (nice and compact) [here](https://wiki.gentoo.org/wiki/Nftables)
* and Arch Linux NFT (alike Gentoo's wiki, but nothing about howto compile kernel :) [wiki](https://wiki.archlinux.org/title/Nftables)

Theory:
* Netfilter framework [at Wikipedia](https://en.wikipedia.org/wiki/Netfilter)

# TODO

Change `nft-helper.sh` parameter names:

* from 'load' to 'sync'

