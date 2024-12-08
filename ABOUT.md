## Project overview

Modern Linux systems use NFT firewall - successor of Iptables. It comes with a new `C structure` alike configuration format ([look: NFT in short 🠋](#nft-in-short)).

Firewall is a crucial security element, thus its configuration should be kept straightforward.

TODO: move it configuration: 
The `NFT List` uses "available-enabled pattern" ([look: Configuration files and directories 🠋🠋🠋](#configuration-files-and-directories)) configuration, that is well known from Apache or Nginx. List resource, such as IPs are read from simple 'line-delimited' text files.

The idea is to avoid mixing NFT configuration with resource lists. Instead, keep them separate, similar to good program design where algorithms and data remain distinct and are not intertwined.

Next points describe how to configure NFT, you can also jump straight to Examples.
