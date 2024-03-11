# NFT Helper - filter traffic by domain names + split configuration
**NOTE:**
Usage of this tool requires knowledge regarding Linux NFT firewall framework.
For more information check out [NFT Quick reference in 10 minutes](https://wiki.nftables.org/wiki-nftables/index.php/Quick_reference-nftables_in_10_minutes).
Additionally, NFT guides with an examples can be found in [Useful links](#useful-links) section at the bottom of this page.


When managing my network I come across the need to restrict a traffic to a given domain name list.
Sounds easy task, just read the list, resolve names and load IPs to a firewall.
It started with a simple Bash script, once when it has been developed, I got other feature. I could keep domain list in a separated file. 'structure' (firewall configuration) now has been separated from data (domain names).

The firewall is NFT, its `C structure` alike configuration ([look bellow 🠋🠋](#a-small-picture)) that I really like now could be extended by text `one domain per line` format files holding e.g. blacklisted domain names.
My script was reading the list, resolving names and passing this information into proper
place in NFT.

Once there has been means to read domain names, next step seem to be a possibility to load IP addresses, and why not mac addresses?
So the program become capable of loading `network resources`, to indicate where within NFT configuration given
resource set should be added I defined keyword `@set`. A bit later come an idea for an `@include` keyword (for including other files) and `@onpanic` for defining policy in the case of network 'emergency'.

NFT by design provides sophisticated functions such as [timeouts](https://wiki.nftables.org/wiki-nftables/index.php/Element_timeouts), [intervals](https://wiki.nftables.org/wiki-nftables/index.php/Intervals), different data types. Additionally IPs resolved from DNS might change over time. Domain name lists (especially blacklists) do change also, etc. One of the 'musts' for a well-made software is a capability to reload configuration keeping in mind all these sophisticated functions of NFT. Thus, the program requirements has grow comparing original 'read list -> resolve names -> load firewall' concept.

NFT comes with Python bindings, it become clear that to continue Bash must be dropped in favor of Python. But in fact, I keep two versions, Bash `NFT Helper Lite` and Pythons `NFT Helper`.

## A small picture
Nftables firewall is configured via `nft` user-space utility, that replaces an old `iptables` but also `ip6tables`, `arptables` and `ebtables` commands. Also it comes also with a new `C structure` alike configuration
file format. Bellow is a simple example:
```
#!/sbin/nft -f
# /etc/nftables.nft

# very simple configuration

define NIC = "eth0"

flush ruleset

table inet my_table {
    set allowed_hosts {
        type ipv4_addr;
    }

    chain input {
        type filter hook input priority 0; policy drop;

        iifname "lo" accept comment "Accept any localhost traffic"
        iifname $NIC tcp dport 80 ip saddr @allowed_hosts accept
    }
}
```
This configuration could be loaded also with:
```

```

As it was told, to do not mix structure with data `NFT Helper` loads configuration from separate file:
```
# /etc/nftdef/allowed_hosts.list
# host that are allowed for connecting this box

@allowed_hosts # load bellow addresses into 'allowed_hosts' set
192.168.0.100 # temperature sensor #1
192.168.0.102 # temperature sensor

```
It's one IP/domain/mac per line file with possibility to comment (`#`) and keywords (`@set`, `@include`, `@onpanic`) instructing `NFT Helper`.

# Project scope

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
3. IPs pointed by DNS can change over time, thus `NFT Helper` runs periodic checks to keep firewall coherent with an actual DNS state.

Please note that domain based filtering is not a perfect one. Usually multiple domain names share common IP's. Encrypted connections (that protect privacy) prevent firewall from inspecting network package for source/destination check. Therefore some extra names can 'sneak' under the radar. However this issue is negligible comparing to benefits coming from restricted firewall rule set.

# NFT sets

NFT comes with [NFT sets](https://wiki.nftables.org/wiki-nftables/index.php/Sets) that allow on grouping elements of the same type together.
For instance, set of type *ipv4_addr* is for grouping IPv4 addresses (192.168.1.1, 192.168.1.2), *ether_addr* for mac addresses (32:9b:92:cd:ce:e8, 02:42:d4:ff:a9:bf) while *ifname* to group network interfaces (enp7s0, br0).

When it comes for NFT Helper, it works on a following Set types:
* *ipv4_addr* for IPv4 and
* *ipv6_addr* for IPv6 elements.

Set is defined within NFT 'table', its scope covers chains and rules defined under table where it has been defined.
Sets can be anonymous, or be named, in the case of `NFT Helper` only named sets are in consideration as `NFT Helper` accesses Sets by a name.

In order to have a set in action, the firewall rule must refer to it defining desired package filtering policy such as drop or accept.
The rule will apply to all set elements.

From another end `NFT helper` fills in Set with a desired addresses.
NFT helper does not create, modify or delete any hooks, chains, or other 'structural' firewall settings. It only operates within NFT sets, 'NFT helper' can only:
* add, or
* remove **elements** of an indicated NFT sets.

It's administrator's job to define firewall configuration. NFT Helper is a tool responsible for filling and keeping sets up to date.

## type and typeof Sets
Set type can be specified as `type`, or `typeof`.
'type' can be an analogy to classes from object oriented languages, for instance *ipv4_addr* and *ipv6_addr* can be represented in Python as:
```
class ipaddress.IPv4Address(address)
class ipaddress.IPv6Address(address)
```

`typeof` is a higher level expression, it defines what is a destiny for elements.
For instance `typeof` can define that IP element should be used as a source address, or destination address:
```
`typeof ip saddr`
`typeof ip daddr`
```
**NOTE:**
NFT Helper does not support `typeof`, it supports only `type` specification limited to *ipv4_addr* and *ipv6_addr*.

# Firewall configuration

NFT configuration should be defined in `/etc/nftables.nft` and in `/etc/nftables.d/`.


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

# References

https://serverfault.com/questions/1145318/nftables-referencing-a-set-from-another-table

# TODO

Change `nft-helper.sh` parameter names:

* from 'load' to 'sync'

