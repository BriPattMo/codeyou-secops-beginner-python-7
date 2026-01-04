# 🧩 Python Assignment: Pulling CMDB Asset Data from an API (JSON)

## Introduction

Security teams can’t protect what they don’t understand. One of the most common “API-driven” security tasks is pulling data from an **asset inventory / CMDB** (Configuration Management Database). This is how teams answer questions like:

* What assets exist in production?
* Which assets are internet-exposed?
* Which teams own the riskiest systems?
* Which high-criticality assets haven’t been seen recently?

In this assignment, you’ll pull CMDB asset data from an API (Mockaroo), parse the JSON, model each asset with a simple class, and generate a risk-focused summary report.

---

## Provided Data Format (Example Record)

Your API returns JSON records shaped like this:

```json
{
  "asset_id": 300,
  "hostname": "finance-4",
  "asset_type": "laptop",
  "os": "Windows",
  "environment": "prod",
  "owner_team": "HR",
  "internet_exposed": true,
  "criticality": "high",
  "last_seen": "11/22/2025"
}
```

---

## Provided Resource

👉 **CMDB API URL:** `PASTE_YOUR_MOCKAROO_URL_HERE`

*(Instructor provides the exact URL.)*

---

# Part 1 — Walkthrough (Guided Build)

## Step 0: Create Your Script

Create a file named:

* `cmdb_api_audit.py`

---

## Step 1: Install + Import Requests

Install (one-time):

```bash
python -m pip install requests
```

Then in your script:

```python
import requests
```

---

## Step 2: Fetch the CMDB Data

```python
API_URL = "PASTE_YOUR_MOCKAROO_URL_HERE"

response = requests.get(API_URL, timeout=10)
print("Status code:", response.status_code)
```

✅ Checkpoint: You should see `Status code: 200`

---

## Step 3: Parse JSON and Inspect Structure

```python
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
```

✅ Checkpoint:

* `Type of data: <class 'list'>`
* Keys like `asset_id`, `hostname`, `internet_exposed`, etc.

---

## Step 4: Create an `Asset` Class

This class models one CMDB record.

```python
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
```

✅ Checkpoint: No errors on run.

---

## Step 5: Convert JSON Records into `Asset` Objects

```python
assets = []
for record in data:
    assets.append(Asset(record))

print("\nFirst asset object:")
print(assets[0] if assets else "No assets")
```

---

## Step 6: Produce a Summary (Counts + Top Findings)

### A) Count assets by environment

```python
env_counts = {}
for a in assets:
    env = a.environment
    env_counts[env] = env_counts.get(env, 0) + 1

print("\n=== Assets by Environment ===")
for env, count in env_counts.items():
    print(env, count)
```

### B) Count by risk level

```python
risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
for a in assets:
    risk_counts[a.risk_level()] += 1

print("\n=== Assets by Risk Level ===")
for k, v in risk_counts.items():
    print(k, v)
```

### C) List internet-exposed assets (hostname + owner + criticality)

```python
exposed = [a for a in assets if a.internet_exposed]

print("\n=== Internet-Exposed Assets ===")
for a in exposed:
    print(f"{a.hostname} | owner={a.owner_team} | crit={a.criticality} | env={a.environment}")
```

---

## Step 7: Write a Report File

Write `cmdb_summary.txt`:

```python
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
```

✅ Checkpoint: file created and contains meaningful output.

---

# Part 2 — Challenge (Required Extensions)

Complete **all** of the following:

## Challenge A: Safer Error Handling

Add `try/except` for network failures:

* connection error
* timeout
* invalid JSON

*(You don’t have to cover every edge case perfectly — the goal is awareness.)*

---

## Challenge B: “High Priority Review” List

Create a filtered list of assets that meet **both**:

* `environment == "prod"`
* AND (`internet_exposed == True` OR `criticality == "high"`)

Print them and include them in the report under a header:

**High Priority Review (Prod + Exposed/Critical)**

---

## Challenge C: Top 3 Owner Teams by Risk

Compute which `owner_team` has the most **HIGH** risk assets.

* Count HIGH risk by team
* Sort descending
* Print top 3 teams and counts
* Include it in the report

---

## Challenge D: Last Seen Age (Stretch but Beginner-Friendly)

If `last_seen` is in the format `MM/DD/YYYY`, calculate how many days ago the asset was seen.

* Add a method: `days_since_seen()` (return an integer or `None` if parsing fails)
* Print a list of assets not seen in **30+ days**
* Include that list in the report

> Tip: use `datetime` from the standard library.

---

# 📦 Deliverables

Submit:

1. `cmdb_api_audit.py`
2. `cmdb_summary.txt`
3. Screenshot or pasted terminal output showing:

* status code
* total assets
* risk summary
* high priority review count/list

---

# ✅ Rubric (50 points)

* **10** — API request works + JSON parsed successfully
* **10** — Uses `Asset` class correctly and computes risk level
* **10** — Correct summary counts + internet-exposed list
* **10** — Challenge B + C completed correctly
* **5** — Challenge A (error handling)
* **5** — Challenge D (last_seen days) implemented correctly or best-effort

---

# 📚 References

* Requests Quickstart:
  [https://requests.readthedocs.io/en/latest/user/quickstart/](https://requests.readthedocs.io/en/latest/user/quickstart/)
* JSON basics in Python (`response.json()` and dict/list use):
  [https://docs.python.org/3/library/json.html](https://docs.python.org/3/library/json.html)
* Python dictionaries (`get`, counting patterns):
  [https://docs.python.org/3/tutorial/datastructures.html#dictionaries](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)
* Sorting in Python (`sorted`, key=):
  [https://docs.python.org/3/howto/sorting.html](https://docs.python.org/3/howto/sorting.html)
* `datetime` parsing (`strptime`) for `last_seen`:
  [https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)
