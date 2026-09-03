#!/usr/bin/env python3
"""Extract proxy-only YAML from Alvin9999 residential IP config files."""
import re
import sys
import urllib.request
import ssl

IPS = {
    "ip1": "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/1/config.yaml",
    "ip2": "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/2/config.yaml",
    "ip3": "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/3/config.yaml",
    "ip4": "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/4/config.yaml",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_and_extract(url):
    """Fetch a full Clash config and extract only the proxies section."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        # Remove \r characters first
        content = r.read().decode("utf-8", errors="replace").replace("\r", "")

    # Extract proxies section (first occurrence only)
    match = re.search(r"^proxies:\s*\n(.*?)(?=\nproxy-groups:|\nrule-providers:|$)", content, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    return "proxies:\n" + match.group(1)

def deduplicate_proxies(yaml_text):
    """Remove duplicate proxy entries based on name."""
    lines = yaml_text.splitlines()
    seen_names = set()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("- name:"):
            name_match = re.match(r"^\s*-\s*name:\s*(.+)$", line)
            if name_match:
                name = name_match.group(1).strip().strip('"').strip("'")
                if name in seen_names:
                    # Skip duplicate block
                    indent = len(line) - len(line.lstrip())
                    i += 1
                    while i < len(lines):
                        cur = lines[i]
                        if cur.strip() and not cur.startswith(" " * (indent + 2)):
                            break
                        i += 1
                    continue
                seen_names.add(name)
        result.append(line)
        i += 1
    return "\n".join(result)

if __name__ == "__main__":
    import json

    output = {}
    for ip_name, url in IPS.items():
        try:
            print(f"Fetching {ip_name} from {url}", file=sys.stderr)
            raw = fetch_and_extract(url)
            if raw:
                clean = deduplicate_proxies(raw)
                output[ip_name] = clean
                count = len(re.findall(r"- name:", clean))
                print(f"  -> extracted {len(clean)} bytes, {count} proxies", file=sys.stderr)
            else:
                print(f"  -> failed to parse", file=sys.stderr)
        except Exception as e:
            print(f"  -> error: {e}", file=sys.stderr)

    with open("/tmp/ip_lists.json", "w") as f:
        json.dump(output, f)
    print("Done.", file=sys.stderr)
