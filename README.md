# NFT List

NFT List provides the functionality for blocking and allowing traffic based on: 
* Domain names
* IPv4 and IPv6 hosts and networks
* Mac addresses

It extends [Linux NFT](https://en.wikipedia.org/wiki/Nftables) firewall and uses [NFT Sets](https://wiki.nftables.org/wiki-nftables/index.php/Sets) to "attach" a specific list. 

It uses "available-enabled pattern" [configuration](#configuration-files-and-directories) known from Apache or Nginx to let administrators on convenient management of access/deny lists.

**This tool enables administrators to separate the NFT firewall configuration logic (defined in `/etc/nftables.*`) from its data - that is access/deny lists.**

`NFT List` resolves domain names by default via CloudFlare's `1.1.1.1` DOH (DNS over HTTP(s)). This tool has been developed in Python, although there is also simplified `bash` version.

**NOTICE: As the firewall is a critical security component, it is essential to review this documentation thoroughly. It has been designed to be concise, with important details emphasized in bold for clarity.**

## Table of contents

- [Overview](#overview)
- [NFT in short](#nft-in-short)
- [Project's scope](#projects-scope)
- [HowTo Use](#howto-use)
  - [Part I: Firewall](#part-i-firewall)
    - [NFT sets](#nft-sets)
    - [NFT Structure](#nft-structure)
  - [Part II: Installation and Configuration](#part-ii-installation-and-configuration)
    - [Installation](#installation)
    - [Configuration files and directories](#configuration-files-and-directories)
      - [File format](#file-format)
    - [Directives](#directives)
    - [Command line](#command-line)
    - [Periodic runs](#periodic-runs)
    - [White List example](#white-list-example)
  - [Troubleshooting](#troubleshooting)
- [Summary](#summary)
- [Useful links](#useful-links)


## Requirements

The `NFT List` requires Python 3 and a configured NFT firewall. Administrators define NFT sets within the firewall, which are populated with the appropriate lists by `NFT List`.

**Short NOTICE: In this document network resources that `NFT List` can refer to (domain names, IPv4/IPv6 and macs) will be referred to as 'resources'.**

## Installation

Project is available in PyPI, tp install it use the following commands (root is requied): 
```commandline
# Install Python package from repository
pip install nftlist
# initialise configuration structure
nftlist init --download
```
Option `--download` downloads pre-defined lists that can be used for restricting firewall to traffic to a specific popular servers, such as GitHub or Cloudflare. The complete list can be seen 
[here](https://github.com/tools200ms/nftlist/tree/release/lists).

## Configuration

`Nft List` configuration is in `/etc/nftlists/`. **Directory `available` is designated for user defined access/deny lists.** 
Directory `enabled` can only be used for linking to lists in `available`. **As the pattern suggests, `NFT List` will load the lists from `enabled` directory**.

The list files must have a `.list` extension. Link file must have the same basename as a source file. `NFT List` does not do recursive search, thus `enabled/directory/link_to_file_in_available.list` is ignored with a warning.

List files in `available` can contain directives `@include` that is described in detail in [directives section](#directives).

This allows on referring to lists located in `included` directory. **Location `included/_user` is designated for "user defined large lists".**

Location `included/_local` holds 'RFC defined' ranges for local network adresses.

Locations `included/<service name>` contain addresses specific for popular services such as GitHub or Cloudflare, let's call it **Popular service lists**.

**NOTICE: Popular service lists are automatically updated to reflect changes in the infrastructure. Administrators should avoid modifying them.**

Below the '/etc/nftlists/' file-directory structure: 
```bash
# tree /etc/nftlists/
/etc/nftlists/
├── available
│   ├── inbound_filter.list
│   └── outbound_filter.list
├── enabled
│   └── inbound_filter.list -> ../available/inbound_filter.list
└── included
    ├── _local
    │   ├── broadcast-ipv4.list
    │   ├── localnet-ipv4.list
    │   └── localnet-ipv6.list
    ├── _user
    ├── bitbucket
    │   ├── bitbucket-all-inet.list
    │   ├── bitbucket-out-inet.list
    │   └── bitbucket-out_email-inet.list
    ├── cloudflare
    │   ├── cloudflare-ipv4.list
    │   └── cloudflare-ipv6.list
    ├── github
    │   ├── github-actions-inet.list
    │   ├── github-api-inet.list
    │   ├── github-git-inet.list
    │   ├── github-hooks-inet.list
    │   ├── github-packages-inet.list
    │   ├── github-pages-inet.list
    │   └── github-web-inet.list
    └── nitropack
        └── nitropack-ipv4.list

9 directories, 19 files
```
The format of '.list' file is described in [Configuration files section](#configuration-files).

## Firewall side (NFT sets)
On NFT side (by default in `/etc/nftables.nft` and `/etc/nftables.d/`) administrator defines firewall configuration. Configuration shall include sets, where `NFT List` attaches apropperiate addresses. See examples in [Examples section](#examples).

**`NFT List` does NOT alter firewall configuration, it ONLY operates (removes, adds) on a set elements.**

### Supported NFT types
`NFT List` accepts a following set types: 
- `ipv4_addr`
- `ipv6_addr`
- `ether_addr`

Details about Set typec can be found in ["Named sets specifications (nftables.org site)"](https://wiki.nftables.org/wiki-nftables/index.php/Sets).

### "Non-atomic" issue
Advantage of NFT over IPtables is 'atomic' operation. The command `nft -f <filename>` loads configuration 'on a side'. When configfile is successfully validated NFT switches in an atomic manner to a new setup. This means there is no a single moment when firewall is partially configured.
As `NFT List` acts after `nft` command, this might bring security issues: 
- very sort time when access to denied IPs is possible as lists has not been fully loaded yet.
- failure to launch `NFT List` that makes deny lists not loaded.
To address this issue `NFT List` enforces to 'cork' a set.

The solution is to cork a sets with `0.0.0.0/0` and `::/128` masks. 
See example below: 
```
table inet filtering_machine {
    set allow_ip_list {
        type ipv4_addr;
        flags timeout;
    }

    set allow_ip6_list {
        type ipv6_addr;
        flags timeout;
    }

    set ban_ip_list {
        type ipv4_addr;
        elements = { 0.0.0.0/0 }
    }

    set ban_ip6_list {
        type ipv6_addr;
        elements = { ::/128 }
    }

    set allow_mac_list {
        type ether_addr;
        flags timeout;
    }
}
```
The allow lists should be left empty (no elements), for filling in bit later by `NFT List`. In this case there us no security thread as firewall would not allow packages (empty set) to pass through. You can put in NFT configuration IP of administrative machine if you suspect the scenario where `NFT List` does not load, to ensure access to machine.

Ban lists are logical opposites to 'allow' lists. To ensure there is no single moments when 'bad' packege can 'sneak under', mask `0.0.0.0/0` and `::/128` should be used to cork all `ipv4_addr` and `ipv6_addr` traffic. `NFT List` will remove that addresses after ban list is loaded.



## Project overview

Modern Linux systems use NFT firewall - successor of Iptables. It comes with a new `C structure` alike configuration format ([look: NFT in short 🠋](#nft-in-short)).

Firewall is a crucial security element, thus its configuration should be kept straightforward.

TODO: move it configuration: 
The `NFT List` uses "available-enabled pattern" ([look: Configuration files and directories 🠋🠋🠋](#configuration-files-and-directories)) configuration, that is well known from Apache or Nginx. List resource, such as IPs are read from simple 'line-delimited' text files.

The idea is to avoid mixing NFT configuration with resource lists. Instead, keep them separate, similar to good program design where algorithms and data remain distinct and are not intertwined.

Next points describe how to configure NFT, you can also jump straight to Examples.

## NFT sets

TODO: remove
Note, `timeout` flag of NFT set can be used to define elements to expire automatically. It might be a good feature for a long, constantly being updated lists. More information in [TODO]().

`NFT List` at each boot chceks if lists are propperly sealed. If a ste is bound to drop or reject, but no '0.0.0.0/0 cork' is added, warning is issued.

## NFT List configuration
...

## Simple example
TODO: move to an end
Simple example can be foundin: [example1.1-workstation.nft](examples/example1.1-workstation.nft) and `NFT List`
[example1.1-workstation.list](examples/example1.1-workstation.list).

Once when NFT with this configuration is loaded (note `flush ruleset` - that purges all previous settings) `allowed_hosts` is empty.
Therefore, no other host is allowed to let in, access can be open from command line:
```bash
nft add element inet my_table allowed_hosts { 172.22.0.2 }
```
or `NFT List` can do this for you. Define file such as:
```
# /etc/nftdef/allowed_hosts.list
# host that are allowed for connecting this box

@set inet my_table allowed_hosts # load bellow addresses into 'allowed_hosts' set
172.22.0.2 # Peer 2
```

and load:
```bash
nftlist.sh update /etc/nftdef/allowed_hosts.list
```
`NFT List` comes with OpenRC init script to load settings a boot time, and cron script for periodic reloads. More in [Part II: Installation and Configuration](#part-ii-installation-and-configuration).



## HowTo Use


### Part I: Firewall
This part explains an interaction of `NFT List` with Nftables user-space tools (firewall).

#### NFT sets

NFT comes with [NFT sets](https://wiki.nftables.org/wiki-nftables/index.php/Sets) that allow on grouping elements of the same type together.
Example definition of NFT set looks as follows:
```
table inet user_defined_table_name {
       set user_defined_set_name {
               type ipv4_addr;
               flags timeout, interval;
               auto-merge;

               elements = { 10.0.0.0/8 }
       }
}
```

Sets can be anonymous, or named. Above example defines named (`user_defined_set_name`) set. 
To have `NFT List` to feed sets with a data it must be obviously named.

NFT defines various types of elements, for instance *ipv4_addr* is for keeping IPv4 addresses, 
*ether_addr* for mac addresses while *ifname* is to group network interfaces (e.g. enp7s0, br0).

`NFT List` operates on a Sets of the following types:
* *ipv4_addr* for IPv4,
* *ipv6_addr* for IPv6 elements
* *ether_addr* for mac addresses

In this document, the list of any type will be defined as `resource list`.

Nftables also provides `typeof` keyword that as documentation states:

> allows you to use a high level expression, then let nftables resolve the base type for you

`NFT List` can operate **only** on sets declared with `type`. Trial of loading data into `typeof`, 
or `type` but of not supported type will fail.

Set can be complemented by flags that specifies more precisely behaviour and format of an elements:
* *timeout* - specifies timeout when a set element is set for expiration, note that various elements within one set can have a different timeouts
* *constant* - set content can not be changed once when it has been bound to a rule
* *interval* - set elements can be intervals, that is IP addresses with network prefixes or address ranges in format: *<first addr>-<last addr>*, e.g.
`192.168.100-192.168.199`

`NFT List` validates these flags and acts as follows:
* *timeout* - `NFT List` resolves IP addresses and adds them to 'timeout set' setting up a default timeout that is 3 days. If the list is refreshed, timeout is updated. If given domain name does not resolve to a certain IP anymore, it will simpli expire and eventually disappear from the set.
* *constant* - `NFT List` acts normally if set is not bound with rule.
* *interval* - `NFT List` extends accepted format by network prefixes and address ranges.


`auto-merge` option of `NFT Set` combines a set elements into intervals, this enables auto-packing addresses into groups. For instance
adding `10.2.0.0/16` and `11.3.0.0/16` merges into one network: `10.2.0.0/15`. 
With `auto-merge` defined the result of `nftlist update` might not only be insertions and removals, but also `merge`, `split` actions.


In NFT there is no type `inet_addr` that would match both types `ipv4_addr` and `ipv6_addr`. Therefore, one set can not
hold mixed IPv4 and IPv6 elements. If set has been defined of a `type ipv4_addr` NFT-List will resolve `A` DNS records to acquire IP.
If set is of `type ipv6_addr` `AAAA` DNS records are queried.


#### NFT Structure

If you inspect an example from [Quick introduction](#quick-introduction) there are three noticeable aspects:
- Sets belong to table
- where chains and finally rules are defined
- rules refer to set to apply a certain policy for a given network resources

Sets are a `meeting` point. `NFT List` fills in Set with a desired IP/mac addresses. 
`NFT List` does not create, modify or delete chains, rules or other 'structural' firewall settings. 
It only operates within sets, 'NFT List' can only:
* add, or 
* remove **elements** of an indicated NFT sets.

It's administrator's job to define a firewall configuration. `NFT List` is a tool designed for filling and keeping set elements up to date.


### Part II: Installation and Configuration
This part is about how to configure the tool.

#### Installation
`NFT list` is in an early development phase, there is no packages developed yet, you can install it by unpacking
release file into `/` directory:
```bash
tar -xzvf nfthelper-1.2.9-alpha.tar.gz -C /
```
this will simply extract `nftlist.sh` to `/usr/local/bin/` and `nftlist` to `etc/init.d/`.

At this point, only OpenRC is supported (no systemd).

Add nftlist to OpenRC's default runlevel:
```bash
rc-update add nftlist default
```
To launch `NFT List` simply start the service:
```bash
service nftlist start
```
this reads configuration from `/etc/nftlists/available/` and loads NFT sets.
Just after installation as configuration is empty nothing will happen.





##### File format

The file format expected by `NFT List` is a text file holding domain/address list, such as:
```
# /etc/nftlists/avaliable/blacklisted_domain.list

@set inet filter blacklist

bad-domain.xxx.com # don't go there
your-bank.login.space # no comment
# aha ...
specialoffernow.info
```

Comments are marked by `\#` symbol.

### Directives

Resource list should or can be proceeded by a directives:

**\@set \<family\>|- \<table name\>|- \<set name\>|-**

Indicates NFT target set for filling, addresses placed below this directive will be loaded to an indicated set.
The directive must define table family, name, and set name. Minus sign (**-**) (`copy sign`) if is used for one or more `\@set`
parameters instructs to apply previous settings (copy previous parameter) e.g.:
```
@set ipv6 - -

# set will apply to: set ipv6 filter allow_outbound
@set - filter allow_outbound

... addresses ...

# set will apply to: set ipv6 filter allow_inbound
@set - - allow_inbound

... addresses ...
```

**\@query \<selector\>**

Do additional DNS query if domain name is encountered, selector indicates query type:
- **\@query subdomain.** - query also subdomain, e.g.:
    > **\@query www.**

    also checks `www.` subdomain for each encountered domain in a current set

**\@include \<file name\>**

Include file, file that is to be included must be located inside `/etc/nftlists/included`.
It does not need to have `.list` extension, it can be compressed, the compression algorithm
must be indicated by a correct extension: `.gz`, `.zip` ...


**\@onpanic keep|discard**

This directive defines an action in the case of `panic` signal. If such an event happen, probably
white lists should be discarded from sets while black addresses keeped.
Panic signal can be issued with:
> nftlist panic

command.


The only required directive is `\@set` that indicates target set. However, 
file's `\@set` directive can be replaced with a command line `--set` 
(or short `-s`) option that does the same. In this case target set does 
not need to be defined in `*.list` configuration file. For more options see command line usage.

## Command line

NFT Sets are updated by `NFT List` each time when revise is started, or reloaded:

```bash
service nftlist start
service nftlist reload
```

`NFT List` can also be called directly from command line:
```bash
# nftlist
Following updates has been found
Id:    action:
 1     add 4 IPv4 elements
        to 'blacklist' set of 'filter' inet table

proceed with update?
      yes    / no / details / help or (y    /n/d/h) - if yes,     update all
  or  yes Ids/ no / details / help or (y Ids/n/d/h) - if yes Ids, update chosen set
 :
```
Typing `yes`, or `y` will proceed with update, update can be limited to a chosen set by passing Id
indicating actions just after `yes`, e.g. `yes 1`, `yes 2 5`.

The prompt can be skipped with:
```bash
# Update Sets without prompt
nftlist update
# or shorter
nftlist u
```
This will proceed with updates without prompting.

By default, configuration from `/etc/nftlists/available/` is loaded, but it can be overwritten:
```bash
nftlist update /etc/my_list.list
# or
nftlist update /etc/my_list_directory/
# additionally include directory can be indicated:
nftlist update /etc/my_list.list --includedir /etc/incl_lists/
# or shortly:
nftlist update /etc/my_list.list -D /etc/incl_lists/
```

Set can be indicated as a command line argument:
```bash
nftlist u --set inet filter allow
# or use short '-s' flag
nftlist u -s inet filter allow
```
If it is provided as command line argument it does not need to be declared in `.list` file.


`nftlist` comes with `panic` option that will apply policies defined by `\@onpanic` directive.


## Periodic runs

`A` or `AAAA` records can change over time, therefore firewall shall be updated periodically.
It is advised to add to daily cron `service nftlist reload` so configuration shall be keep in
sync with DNS entries.

## White List example

One of the example of whitelisting is to allow outgoing connections to be only possible with a
very limited number of servers. This can be a list of a domain names that are used for system updates.
The configuration might look as bellow:
```
# file: /etc/nftlists/available/repo_devuan.list

# Devuan repositories
deb.devuan.org
deb.debian.org
```
```
# file: /etc/nftlists/enabled/

@set inet filter allow_outgoing
@include repo_devuan.list
```
We can whitelist more resources:
```
# file: /etc/nftlists/enabled/

@set inet filter allow_outgoing
@include repo_devuan.list

10.2.0.100
example.com
```
Note that by splitting configuration to a set of files it become more manageable.
Also note, that you can mix domain names with IP address.

NFT rule bound to `allow_outgoing` set would be defined in forward chain. The default policy for that chain might be `drop`, the
rule might be as follows:
```
iifname br0 oifname eth0 ip daddr @allow_outgoing tcp dport { 80, 443 } accept
```


## Troubleshooting
In the case of troubles you run:
```
nftlist --verbose
```
And check for any detailed error messages. If it does not help analyze what exactly is under the hood:

```bash
# Stop firewall
service nftlist stop
service nftables stop

# checkout defined rules
# it should be empty
nft list ruleset

# start firewall
service nftables stop

# analyze configuration
nft list ruleset

# start nftlist
service nftlist start

# and verify if sets has been updated
nft list ruleset
```
also you can:
```bash
# List all sets
nft list sets

# Add set elements manually
nft add element inet my_table allowed_hosts { 172.22.0.2 }
```
NFT provides [counters](https://wiki.nftables.org/wiki-nftables/index.php/Counters), it can give you some information if
traffic is passing through a certain firewall rule or hook.
In tha case of troubles tools such as tcpdump and WireShark come in handy.

# NFT advanced features

NFT by design provides sophisticated functions such as [timeouts](https://wiki.nftables.org/wiki-nftables/index.php/Element_timeouts), [intervals](https://wiki.nftables.org/wiki-nftables/index.php/Intervals), 
different data types. Additionally, IPs resolved from DNS might change over time. Domain name lists (especially blacklists) do change also, etc. One of the 'musts' for a well-made software is a capability to reload configuration keeping in mind all these sophisticated functions of NFT. 
Thus, the program requirements has grow comparing original 'read list -> resolve names -> load firewall' concept.


# Summary

`NFT List` can be used in: 
- virtualise environments to
is useful with containerization/virtualization technics where running VMs can be limited to exact network resources they need. It has been developed as a lite, robust and straightforward solution for various firewall configuration cases.

# Useful links

**HowTo:**

* Nftables Wiki [here](https://wiki.nftables.org/)
* Gentoo Nftables guide (nice and compact) [here](https://wiki.gentoo.org/wiki/Nftables)
* and Arch Linux NFT (alike Gentoo's wiki, but nothing about howto compile kernel :) [wiki](https://wiki.archlinux.org/title/Nftables)

**Theory:**

* Netfilter framework [at Wikipedia](https://en.wikipedia.org/wiki/Netfilter)

**Administration**

* Using iptables-nft: a hybrid Linux firewall [at Redhat.com](https://www.redhat.com/en/blog/using-iptables-nft-hybrid-linux-firewall)
* [serverfault: nftables: referencing a set from another table](https://serverfault.com/questions/1145318/nftables-referencing-a-set-from-another-table)

**Bad addresses databases**

* Phishing Database: [github: mitchellkrogza/Phishing.Database](https://github.com/mitchellkrogza/Phishing.Database/)

**Programming**

* fw4 Filtering traffic with IP sets by DNS [Openwrt.org](https://openwrt.org/docs/guide-user/firewall/filtering_traffic_at_ip_addresses_by_dns)
* Python Nftables tutorial: [GitHub](https://github.com/aborrero/python-nftables-tutorial)
