import requests

# Fetch the CMDB Data
API_URL = "https://my.api.mockaroo.com/ironclad/cmdb.json?key=cf7bbbd0"

response = requests.get(API_URL, timeout=10)
print("Status code:", response.status_code)

# Parse JSON and Inspect Structure
if response.status_code != 200:
    print("Request failed:", response.status_code)
    print("Response preview:", response.text[:200])
    raise SystemExit

data = response.json()
print("Type of data:", type(data))

if isinstance(data, list) and data:
    print("Number of assets:", len(data))
    print("Fields available:", list(data[0].keys()))
    print("First asset preview:", data[0])
else:
    print("Unexpected JSON structure. Expected a list of assets.")
    raise SystemExit

# Create an Asset Class
class Asset:
    def __init__(self, raw: dict):
        self.raw = raw
        self.asset_id = raw.get("asset_id")
        self.hostname = raw.get("hostname", "unknown")
        self.asset_type = raw.get("asset_type", "unknown")
        self.os = raw.get("os", "unknown")
        self.environment = raw.get("environment", "unknown")
        self.owner_team = raw.get("owner_team", "unknown")
        self.internet_exposed = bool(raw.get("internet_exposed", False))
        self.criticality = raw.get("criticality", "low")
        self.last_seen = raw.get("last_seen", "unknown")

    def risk_level(self) -> str:
        """
        A simple (not perfect) risk rule set:
        - HIGH if internet_exposed AND criticality is high
        - MEDIUM if internet_exposed OR criticality is high
        - LOW otherwise
        """
        crit_high = str(self.criticality).lower() == "high"
        if self.internet_exposed and crit_high:
            return "HIGH"
        if self.internet_exposed or crit_high:
            return "MEDIUM"
        return "LOW"

    def __str__(self) -> str:
        return (f"{self.hostname} ({self.asset_type}, {self.os}, {self.environment}) "
                f"owner={self.owner_team} exposed={self.internet_exposed} "
                f"crit={self.criticality} last_seen={self.last_seen} risk={self.risk_level()}")
    
# Convert JSON Records into Asset Objects
assets = []
for record in data:
    assets.append(Asset(record))

print("\nFirst asset object:")
print(assets[0] if assets else "No assets")

# Produce a Summary (Counts + Top Findings)
#  Count assets by environment
env_counts = {}
for a in assets:
    env = a.environment
    env_counts[env] = env_counts.get(env, 0) + 1

print("\n=== Assets by Environment ===")
for env, count in env_counts.items():
    print(env, count)

# Count by risk level
risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
for a in assets:
    risk_counts[a.risk_level()] += 1

print("\n=== Assets by Risk Level ===")
for k, v in risk_counts.items():
    print(k, v)

#List internet-exposed assets (hostname + owner + criticality)
exposed = [a for a in assets if a.internet_exposed]

print("\n=== Internet-Exposed Assets ===")
for a in exposed:
    print(f"{a.hostname} | owner={a.owner_team} | crit={a.criticality} | env={a.environment}")

# Write a Report File
with open("cmdb_summary.txt", "w", encoding="utf-8") as out:
    out.write("Ironclad CMDB API Audit Report\n")
    out.write("==============================\n")
    out.write(f"URL: {API_URL}\n")
    out.write(f"Status: {response.status_code}\n")
    out.write(f"Total assets: {len(assets)}\n\n")

    out.write("Assets by Environment:\n")
    for env, count in env_counts.items():
        out.write(f"- {env}: {count}\n")

    out.write("\nAssets by Risk Level:\n")
    for level, count in risk_counts.items():
        out.write(f"- {level}: {count}\n")

    out.write("\nInternet-Exposed Assets:\n")
    for a in exposed:
        out.write(f"- {a.hostname} | owner={a.owner_team} | crit={a.criticality} | env={a.environment}\n")

print("\nWrote report to cmdb_summary.txt")