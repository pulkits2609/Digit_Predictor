"""Exit successfully only when a supplied API origin reports ready."""
import argparse
import json
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("origin", help="API origin, e.g. https://api.example.com")
args = parser.parse_args()
try:
    with urllib.request.urlopen(args.origin.rstrip("/") + "/readyz", timeout=15) as response:
        print(json.dumps(json.load(response), indent=2))
except (urllib.error.URLError, ValueError) as exc:
    parser.exit(1, f"API is not ready: {exc}\n")
