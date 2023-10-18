# NFT Helper - filter trafic by domain names
This set of scripts basing on a domain name list resolves its IP's and updates NFT firewall accordingly.

It makes posible for instance to limit outboud connectins from continer to IPs used by disribution repositories. Therefore, continer's outboud connectivity can be lockup exactly into recources it nedds - repositories for updates.

I tested this script with Alpine and OpenRC, the configuration looks as follows: 
/etc/init.d/nft-update - OpenRC script to add filtering rules
/etc/nftsets/ - directory holding domain name and IP's lists
/root/bin/nft-update-sets.sh - main script that does domain name resolution and sets NFT

Domain names are resolved using CloudFlares 1.1.1.1 DOH (DNS over HTTP(s)) server. This is accually the most secure way to query domain names.

## How to
First define aproperiate NFT set, for instnce: 
```
table inet filter {
       set crepo4http {
               type ipv4_addr ;
               flags timeout ;
       }
}
```
Script must be 'aware' of table name, chain type and set name, so the list of domains can be added to aproperiate set (after resolving into IP). Therefore. the configuration file should have strict name, for instance:
/etc/nftsets/inet-filter-crepo4http.list
\<table name>-<chain type>-<set name>.list

The content of the file might be: 
```
# Devuan repository for continer upodates
deb.devuan.org
deb.debian.org
```

Comments starting with \# can be used, also, if you need you can pleace an IPv4 or IPv6 adress, eg:
>\# Devuan repository for continer upodates
>deb.devuan.org  
>deb.debian.org
> \# IP address will be passed straight to NFT
>146.75.118.132

`nft-update start` reads configuration files launces /root/bin/nft-update-sets.sh which resolves domain names and updates proper NFT sets.

## Testing
You can see what NFT commands /root/bin/nft-update-sets.sh would call by `PRETEND` variable to 'yes'
```
PRETEND=yes /root/bin/nft-update-sets.sh tablef filter testset /etc/nftsets/tablef-filter-testset.list
```
