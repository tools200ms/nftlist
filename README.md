# scripts
Various shell scripts

## nft-update-sets.sh
Updates NFT set by IP's to which domains defined in file resolve to.

As an example: 
Content of: /etc/nftsets/lxc-allowed-out.list

> # Devuan repository: 
> deb.devuan.org

You can use comments by precceding text by **#**
Launch: 
> nft-update-sets.sh inet filter lxcrepo4 /etc/nftsets/lxc-allowed-out.list
to update lxcrepo4 set that is defined in filter chain of inet table.

or call
> PRETEND=on nft-update-sets.sh inet filter lxcrepo4 /etc/nftsets/lxc-allowed-out.list
to see what nft commands script would call.
