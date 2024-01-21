# NFT Helper - filter traffic by domain names
NFT Helper scripts has been developed to add domain name filtering capabilities to NFT firewall.
Desired domain names are read from configuration file, names are resolved to IP's that is used to
update NFT - thus to limit traffic to a specified domain set.

It's not a perfect filtering as usually different domain names share common IP's. Encrypted connections prevent firewall from inspecting package to validate destination domain. Therefore some extra names can 'sneak' under the radar. However this issue is negligible comparing to benefits coming from restricted firewall ruleset.

NFT Helper is useful with containerization/virtualisation technics where running VMs can be limited to exact network resources they need.

NFT Helper is a set of scripts developed for Alpine Linux:
`/etc/init.d/nft-helper` - OpenRC script to be launched in 'default' runlevel
`/etc/periodic/daily/nft-helper.daily.sh` - script to be launched daily (preferably) to refresh IP list
`/usr/local/bin/nft-helper.sh` - finally the main script that does domain name resolution and sets NFT

Configuration for NFT-helper that is a set of files holding the list of domain names is designed to be placed in
```
/etc/nftdef/
```
directory. The files should end with `*.list` extension to be loaded.


**NOTE 1:**
Domain names are resolved using CloudFlare 1.1.1.1 DOH (DNS over HTTP(s)) server. This is actually the most secure way to query domain names.


**NOTE 2:**
`A` or `AAAA` records can change over time, therefore firewall shall be updated periodically. This is the role for the script `/etc/periodic/daily/nft-helper.daily.sh`.

## Configuration
IP addresses are grouped within `NFT sets`, sets are defined as a part of a firewall table. To learn NFT, NFT Quick reference in 10 minutes [here](https://wiki.nftables.org/wiki-nftables/index.php/Quick_reference-nftables_in_10_minutes).

### 1. Define NFT set to be feed by NFT-helper
Define a set such as:

```
table inet filter {
       set crepo4http {
               type ipv4_addr ;
               flags timeout ;
       }
}
```
This can be added to `/etc/nftables.nft` or preferably dropped as a separate configuration in `/etc/nftables.d/` directory.

To reload configuration do:
```bash
service nftables reload
```

**NOTE 3:**
Set specification `typeof` is not supported yet, please use `type` for any sets to be feed by 'nft-helper'.

NFT sets should be bound with an appropriate chain rules that implement black/white listing policy, for instance:
```
table inet filter {
        ...
        chain forward {
                type filter hook forward priority filter; policy drop;
                ...
                iifname $NIC_BR0 oifname $NIC_EXT ip daddr @crepo4http tcp dport {http, https} counter accept
        }
        ...
}
```
Above snippet defines the rule that do `accept` only `http` traffic to IPs defined in `crepo4http` set.

### 2. Define domain list

Create in `/etc/nftdef/` file with a name matching the following pattern:
```
<address family>-<table name>-<set name>.list
```

Regarding to an example it might be:
```
/etc/nftsets/inet-filter-crepo4http.list
```

The content of the file might be:
```
# Devuan repository to let on container updates

deb.devuan.org
deb.debian.org

 # IP address will be passed straight to NFT
146.75.118.132
```

Optional comments are indicated by preceding them with \#. You can mix domain names and IP address.
IPv4 and IPv6 are also acknowledged by NFT-helper.
However, ensure that `type` specification of IP set matches provided address family, e.g. if `type ipv4_addr` is defined, adding IPv6 address to set will fail.
Depending on what type is defined, NFT-helper resolves:

* `A` DNS records for `type ipv4_addr`
* `AAAA` DNS records for `type ipv6_addr`
* `A` and `AAAA` DNS records for `ether_addr`

### 3. Feed NFT with data

To feed NFT set call `nft-helper.sh`:
```
nft-helper.sh init inet filter crepo4http /etc/nftsets/inet-filter-crepo4http.list
```
This will query domain names defined in `/etc/nftsets/inet-filter-crepo4http.list` and feed `crepo4http` set with resolved IP's.
If `inet-filter-crepo4http.list` holds IP adresses, it will just copy them to IP set.

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
ensure that `/etc/nftdef/` holds ip/domain list saved in files that match following pattern:
```
<address family>-<table name>-<set name>.list
```
and bellow command:
```
service nft-helper start
```
should start nft-helper.

### 4. NFT updates

There is a probability that some IP addresses might not be associated with a certain domain anymore.
While other new IP's might be added.

`nft-helper.sh` comes with `update` option and cron script for periodic IP updates. It is recommended to
lookup for a domain name once per day to give a chance for a smooth firewall update.
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

Enjoy!
