import requests
from datetime import datetime, date

# Fetch the CMDB Data
API_URL = "https://my.api.mockaroo.com/ironclad/cmdb.json?key=cf7bbbd0"

# Challenge A: Safer error handling
try:
    response = requests.get(API_URL, timeout=10)
    print("Status code:", response.status_code)

except requests.exceptions.Timeout:
    print("Error: Request timed out.")
    raise SystemExit

except requests.exceptions.ConnectionError:
    print("Error: Connection error.")
    raise SystemExit

except requests.exceptions.RequestException as e:
    print("Error: Network request failed:", e)
    raise SystemExit

# Parse JSON and Inspect Structure
if response.status_code != 200:
    print("Request failed:", response.status_code)
    print("Response preview:", response.text[:200])
    raise SystemExit

try:
    data = response.json()
except ValueError:
    print("Error: Invalid JSON received from the API.")
    print("Response preview:", response.text[:200])
    raise SystemExit

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
        - HIGH if internet_exposed AND criticalality is high
        - MEDIUM if internet_exposed OR criticality is high
        - LOW otherwise
        """
        crit_high = str(self.criticality).lower() == "high"
        if self.internet_exposed and crit_high:
            return "HIGH"
        if self.internet_exposed or crit_high:
            return "MEDIUM"
        return "LOW"

    # Challenge D: Last Seen Age (days since last_seen)
    # If last_seen is MM/DD/YYYY, return how many days ago it was seen.
    # Return None if parsing fails.
    def days_since_seen(self):
        try:
            last_seen_date = datetime.strptime(str(self.last_seen), "%m/%d/%Y").date()
            return (date.today() - last_seen_date).days
        except (ValueError, TypeError):
            return None

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
# Count assets by environment
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

# List internet-exposed assets (hostname + owner + criticality)
exposed = [a for a in assets if a.internet_exposed]

print("\n=== Internet-Exposed Assets ===")
for a in exposed:
    print(f"{a.hostname} | owner={a.owner_team} | crit={a.criticality} | env={a.environment}")

# Challenge B: "High Priority Review" list
# Criteria:
# - environment == "prod"
# - AND (internet_exposed == True OR criticality == "high")
high_priority_review = []
for a in assets:
    is_prod = str(a.environment).lower() == "prod"
    is_exposed = a.internet_exposed is True
    is_crit_high = str(a.criticality).lower() == "high"

    if is_prod and (is_exposed or is_crit_high):
        high_priority_review.append(a)

print("\n=== High Priority Review (Prod + Exposed/Critical) ===")
for a in high_priority_review:
    print(f"{a.hostname} | owner={a.owner_team} | crit={a.criticality} | exposed={a.internet_exposed} | env={a.environment}")

# Challenge C: Top 3 Owner Teams by Risk (HIGH only)
# Count how many HIGH risk assets each owner_team has
high_risk_by_team = {}
for a in assets:
    if a.risk_level() == "HIGH":
        team = a.owner_team
        high_risk_by_team[team] = high_risk_by_team.get(team, 0) + 1

# Sort teams by HIGH risk count (descending) and take top 3
top_3_teams = sorted(high_risk_by_team.items(), key=lambda item: item[1], reverse=True)[:3]

print("\n=== Top 3 Owner Teams by HIGH Risk ===")
if top_3_teams:
    for team, count in top_3_teams:
        print(f"{team}: {count}")
else:
    print("No HIGH risk assets found.")

# Challenge D: List assets not seen in 30+ days
# Use days_since_seen(); if it returns a number and it's >= 30, include it
stale_assets_30_plus = []
for a in assets:
    days = a.days_since_seen()
    if days is not None and days >= 30:
        stale_assets_30_plus.append((a, days))

print("\n=== Assets Not Seen in 30+ Days ===")
if stale_assets_30_plus:
    for a, days in stale_assets_30_plus:
        print(f"{a.hostname} | owner={a.owner_team} | last_seen={a.last_seen} | days_ago={days} | env={a.environment}")
else:
    print("No assets found that are 30+ days since last_seen (or dates were unparseable).")

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

    # Challenge B: High Priority Review
    out.write("\nHigh Priority Review List\n")
    out.write("--------------------------------------------\n")
    if high_priority_review:
        for a in high_priority_review:
            out.write(f"- {a.hostname} | owner={a.owner_team} | crit={a.criticality} | exposed={a.internet_exposed} | env={a.environment}\n")
    else:
        out.write("- None found\n")

    # Challenge C: Top 3 Owner Teams by HIGH Risk
    out.write("\nTop 3 Owner Teams by HIGH Risk\n")
    out.write("--------------------------------------------\n")
    if top_3_teams:
        for team, count in top_3_teams:
            out.write(f"- {team}: {count}\n")
    else:
        out.write("- No HIGH risk assets found\n")

    # Challenge D: Last Seen Age: Assets Not Seen in 30+ Days
    out.write("\nAssets Not Seen in 30+ Days\n")
    out.write("--------------------------------------------\n")
    if stale_assets_30_plus:
        for a, days in stale_assets_30_plus:
            out.write(f"- {a.hostname} | owner={a.owner_team} | last_seen={a.last_seen} | days_ago={days} | env={a.environment}\n")
    else:
        out.write("- None found (or last_seen dates were not in MM/DD/YYYY)\n")

print("\nWrote report to cmdb_summary.txt")
