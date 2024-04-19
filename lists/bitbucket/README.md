# Bitbucket/Atlassian IP-range list


To acquire all Atlassian IP-ranges:
```bash
ATL_IPRANGE_JSON_PATH=$(mktemp --suffix=-atlassian-iprange.json)

curl -s https://ip-ranges.atlassian.com/ -o $ATL_IPRANGE_JSON_PATH

cat $ATL_IPRANGE_JSON_PATH | jq -r '.items[].cidr' > bitbucket-all-inet.list
```

Documentation: [here](https://ip-ranges.atlassian.com/)

API: [https://ip-ranges.atlassian.com/](https://ip-ranges.atlassian.com/)

