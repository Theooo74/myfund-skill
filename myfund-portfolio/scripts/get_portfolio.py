#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests

def fetch_portfolio_for(api_key, portfel, fmt="json"):
    url = "https://myfund.pl/API/v1/getPortfel.php"
    params = {"apiKey": api_key}
    if portfel:
        params["portfel"] = portfel
    if fmt:
        params["format"] = fmt

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()

    try:
        return resp.json()
    except ValueError:
        return resp.text

def main():
    api_key = os.environ.get("MYFUND_API_KEY")
    if not api_key:
        print("Error: MYFUND_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(2)

    parser = argparse.ArgumentParser(description="Fetch portfolio(s) from myFund.pl using MYFUND_API_KEY.")
    parser.add_argument("--portfel", help="Portfel (np. 'IKE' lub 'IKE,Oszczędnościowe,Poduszka')")
    parser.add_argument("--format", default="json", choices=["json", "text"], help="Format odpowiedzi (json lub text)")
    args = parser.parse_args()

    portfel_arg = args.portfel
    portfel_list = []
    if portfel_arg:
        portfel_list = [p.strip() for p in portfel_arg.split(",") if p.strip()]
    if not portfel_list:
        portfel_list = ["IKE"]

    results = {}
    for pf in portfel_list:
        try:
            data = fetch_portfolio_for(api_key, pf, args.format)
            results[pf] = data
        except Exception as e:
            results[pf] = {"error": str(e)}

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
