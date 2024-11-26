# NFT List

NFT List provides the functionality for blocking and allowing traffic based on: 
* Domain names
* IPv4 and IPv6 hosts and networks
* Mac addresses

It extends [Linux NFT (Nftables)](https://en.wikipedia.org/wiki/Nftables) firewall and uses [NFT Sets](https://wiki.nftables.org/wiki-nftables/index.php/Sets) to "attach" a specific list. 

It implements the "available-enabled pattern" configuration (refer to the [Configuration section](#configuration)), commonly used in Apache or Nginx, allowing administrators to manage system conveniently.

**This tool enables administrators to separate the NFT firewall configuration logic (defined in `/etc/nftables.*`) from its data - that is access/deny lists.**

`NFT List` resolves domain names by default via CloudFlare's `1.1.1.1` DOH (DNS over HTTP(s)). The tool is implemented in Python.

**NOTICE: As the firewall is a critical security component, it is essential to review this documentation thoroughly. It has been designed to be concise, with important details emphasized in bold for clarity.**

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Firewall side (NFT sets)](#firewall_side__NFT_sets_)
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

**Short NOTICE: In this document network resources handled by `NFT List` (domain names, IPv4/IPv6 and macs) will be referred simply as 'resources'.**

## Installation

Project is available in PyPI, to install it use the following commands (root is required): 
```commandline
# Install Python package from repository: 
pip install nftlist
# initialise configuration: 
nftlist init --download
```
Option `--download` downloads pre-defined lists that can be used for restricting firewall to traffic to a specific popular servers, such as GitHub or Cloudflare. The complete list can be seen 
[here](https://github.com/tools200ms/nftlist/tree/release/lists).

## Configuration
`Nft List` configuration is in `/etc/nftlists/`. The file-directory structure is as follows: 
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
# .... GitHub IP's *.list files
    └── nitropack
        └── nitropack-ipv4.list
```
**Directory `available` is designated for user defined access/deny lists.** 
Directory `enabled` can only be used for linking to lists in `available`. **As the pattern suggests, `NFT List` loads the lists solely from the `enabled` directory**.

List files are required to have a `.list` extension, and link files in `enabled` must share the same basename as their corresponding source files. `NFT List` does not perform recursive searches; therefore, paths like *enabled/directory/link_to_file_in_available.list* are ignored with a warning.

Files `*.list` contain defined resources, potential comments, but also `section marks` and `directives` (details in section ["File Format"](#file-format)). One of the directives is `@include` that allows on inclusion of pre-defined lists from services such as GitHub. These lists are located under `included` directory.

**Location `included/_local` is intended for dropping a large 'user-defined' lists'. That are later 'included' with `@include` directive (in `enabled/` defined list). To activate a list, it must be enabled by creating a symbolic link in the enabled directory.**


## Firewall side (NFT sets)
On NFT side (by default in `/etc/nftables.nft` and `/etc/nftables.d/`) administrator defines firewall configuration. Configuration shall include sets, where `NFT List` attaches appropriate resources. See examples in [Examples section](#examples).

`NFT List`  **does not modify the firewall configuration;** it strictly **manages ONLY elements** within NFT sets.


### "Non-atomic" issue
Advantage of NFT over IPtables is 'atomic' operation. The command `nft -f <filename>` loads configuration 'on a side'. When configfile is successfully validated NFT switches in an atomic manner to a new setup. This means there is no a single moment when firewall is partially configured.
As `NFT List` acts after `nft` command, this might bring following security issues: 
- very short time of security violation (such as open access from denied IPs)
- permanent time of security violation

The first case is difficult to exploit (but still possible), it is due to a short time that is after NFT setup, but before lists are loaded. The second that is a very serious is the result of no-loading `NFT List` due to some kind of system error. 

### Set Corks convention
The solution is to *cork* a sets in NFT configuration with `0.0.0.0/0` and `::/128` masks. Hence, Nftables treats all IP's as blacklisted. **After wards, while `NFT List` loads the list, also removes `0.0.0.0/0` and `::/128` corks**. 

**`NFT List` at launch traverses the list and rules to issue warnings about potentially 'opened' rules.**

**Notice**, there are only **deny 'lists' that must be 'corked'** in oppose to **access lists that can be empty**.

This has been called **'cork' convention**, below there is a snippet demonstrating idea: 
```
table inet filtering_machine {
    set allow_ip_list {
        type ipv4_addr;
        flags timeout;
    }

    set ban_ip_list {
        type ipv4_addr;
        elements = { 0.0.0.0/0 }
    }
    
    table inet machine {
      .......
      chain input {
        type filter hook input priority 0; policy drop;
        ........
        # for 'allow' list ampty set is OK
         iifname eth0 tcp dport 22 \
                        ip  saddr @allow_ip_list ct state new accept
    }
    .......
    chain forward {
      type filter hook forward priority 0; policy allow;
        ........
        # more secure is to "ban all" with 'daddr 0.0.0.0/0 drop'
        ip daddr eth1 oifname eth0 \
              ip daddr @ban_ip_list drop
        ip saddr $LAN_NET iifname $LAN_NIC accept
    }
}
```
In example above, by default we tread all forwarded traffic as banned. And also, by default we don't let any IP establishing connection at input.

Notice, administrators can add extra rules to open access from administrative IPs, that is fixed it Nftables configuration. It ensures access for them in the case if NFT List is not loaded.

### Allow/deny awarnes
Policy of using cork addresses let `NFT List` to be 'aware' of which list is allow, which deny. This is usefull with 'panic' option described in ["NFT List options"](#nft_list_options).

### Supported NFT types
`NFT List` accepts a following element types: 
- `ipv4_addr`
- `ipv6_addr`
- `ether_addr`

Details about Set types can be found in ["Named sets specifications (nftables.org site)"](https://wiki.nftables.org/wiki-nftables/index.php/Sets).

## '.list' file format


## Project overview

Modern Linux systems use NFT firewall - successor of Iptables. It comes with a new `C structure` alike configuration format ([look: NFT in short 🠋](#nft-in-short)).

Firewall is a crucial security element, thus its configuration should be kept straightforward.

TODO: move it configuration: 
The `NFT List` uses "available-enabled pattern" ([look: Configuration files and directories 🠋🠋🠋](#configuration-files-and-directories)) configuration, that is well known from Apache or Nginx. List resource, such as IPs are read from simple 'line-delimited' text files.

The idea is to avoid mixing NFT configuration with resource lists. Instead, keep them separate, similar to good program design where algorithms and data remain distinct and are not intertwined.

Next points describe how to configure NFT, you can also jump straight to Examples.



## NFT List configuration
The file format expected by `NFT List` is a text file holding domain name and address list, such as:
```
# /etc/nftlists/avaliable/blacklisted_domain.list

=set inet filter blacklist

bad-domain.xxx.com # don't go there
your-bank.trustme-login.space # no comment
# aha ...
specialoffernow.info
=end
```

Comments are marked by `\#` symbol.

### Section marks and directives

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

**\@include \<file name\>**

Include file, file that is to be included must be located inside `/etc/nftlists/included`.
It does not need to have `.list` extension, it can be compressed, the compression algorithm
must be indicated by a correct extension: `.gz`, `.zip` ...

**\@query \<selector\>**
**\@end**
Do additional DNS query if domain name is encountered, selector indicates query type:
- **\@query subdomain.** - query also subdomain, e.g.:
    > **\@query www.**

    also checks `www.` subdomain for each encountered domain in a current set


**\@onpanic keep|drop|rise**
**\@end**
This directive defines an action in the case of `panic` signal. If such an event happen, probably
white lists should be discarded from sets while black addresses keeped.
Panic signal can be issued with:
> nftlist panic

command.


The only required directive is `\@set` that indicates target set. However, 
file's `\@set` directive can be replaced with a command line `--set` 
(or short `-s`) option that does the same. In this case target set does 
not need to be defined in `*.list` configuration file. For more options see command line usage.


#### Usage
Once when `nftlist` Python package is installed systemd or OpenRC service is added to init system and enabled. To star service use: 
```bash
service nftlist start
```
It can be used from commandline, for details check with: 
```bash
nftlist --help
```

#### Periodic refresh
`pip install nftlist` also adds script for daily cron tasks. 

#### Panic signal
In the case of signal that securit branch had occured NFT List can aplly 'panic' policy. This will drop elements from allow lists, replace deny with 'any host'(0.0.0.0/0 and ::/128) addresses and apply `@onpanic` directives.


## Examples
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

# TODO

* move `/etc/nftlist/included` to more aproperiate location such as `/var/lib/nftlist/`
* compress "include" resources, think about checksum chek.
* Extend `NFT List` by NFT maps, and vmaps.
* replace `includes/_local/*` path with a keyword that does include appropriate RFC standard.

# Summary

`NFT List` can be used in: 
- virtualize environments to
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
