# GitHub IP-range list

This is how to download most important IP-range lists (for \[web\]hooks, API calls, etc.) used by GitHub.


Bellow, how the lists can be acquired:

```bash
GITHUB_METAAPI_JSON_PATH=$(mktemp --suffix=-github-metaapi.json)
curl -s https://api.github.com/meta -o $GITHUB_METAAPI_JSON_PATH

cat $GITHUB_METAAPI_JSON_PATH | jq -r '.hooks[]' > github-hooks-inet.list
cat $GITHUB_METAAPI_JSON_PATH | jq -r '.web[]' > github-web-inet.list
cat $GITHUB_METAAPI_JSON_PATH | jq -r '.api[]' > github-api-inet.list
cat $GITHUB_METAAPI_JSON_PATH | jq -r '.git[]' > github-git-inet.list
cat $GITHUB_METAAPI_JSON_PATH | jq -r '.packages[]' > github-packages-inet.list
cat $GITHUB_METAAPI_JSON_PATH | jq -r '.pages[]' > github-pages-inet.list
cat $GITHUB_METAAPI_JSON_PATH | jq -r '.actions[]' > github-actions-inet.list

rm $GITHUB_METAAPI_JSON_PATH
```


For GitHub documentation see [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-githubs-ip-addresses)
