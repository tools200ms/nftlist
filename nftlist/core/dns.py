import httpx
import asyncio

import ipaddress

class DNS:
    def __init__(self):
        pass

  #  def query(self): ipaddress

#        return None

CLOUDFLARE_DOH_URL = "https://1.1.1.1/dns-query"


async def resolve(domain_name: str, entry_type: str = "A") -> dict:
    """
    Resolve a domain name using Cloudflare's DNS over HTTPS (DoH) server asynchronously.

    :param domain_name: The domain name to resolve (e.g., "example.com").
    :param entry_type: The DNS entry type to query (e.g., "A", "AAAA", "CNAME", "TXT").
    :return: A dictionary containing the resolved data or an error message.
    """
    headers = {
        "Accept": "application/dns-json"
    }
    params = {
        "name": domain_name,
        "type": entry_type
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(CLOUDFLARE_DOH_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return {
                "domain": domain_name,
                "entry_type": entry_type,
                "data": data.get("Answer", []),
                "status": data.get("Status", None),
                "error": None
            }
        except httpx.HTTPStatusError as http_err:
            return {"domain": domain_name, "entry_type": entry_type, "data": [], "status": None, "error": str(http_err)}
        except Exception as err:
            return {"domain": domain_name, "entry_type": entry_type, "data": [], "status": None, "error": str(err)}


# Example Usage
async def main():
    result = await resolve("example.com", "A")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

