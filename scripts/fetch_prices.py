"""Récupère le dernier cours de clôture de chaque symbole de tickers.txt -> prices.json"""
import json, sys, time, datetime, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "prices.json"
tickers = [l.strip() for l in (ROOT / "tickers.txt").read_text().splitlines()
           if l.strip() and not l.startswith("#")]
prices = (json.loads(OUT.read_text()).get("prices", {}) if OUT.exists() else {})

def fetch(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.load(r)["chart"]["result"][0]
            for ts, c in reversed(list(zip(res["timestamp"], res["indicators"]["quote"][0]["close"]))):
                if c is not None:
                    d = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).date().isoformat()
                    return round(c, 4), d
        except Exception as e:
            print(f"{sym} essai {i+1}: {e}", file=sys.stderr)
            time.sleep(3 * (i + 1))
    return None

ok = 0
for s in tickers:
    r = fetch(s)
    if r:
        prices[s] = {"p": r[0], "d": r[1]}
        ok += 1
        print(f"{s}: {r[0]} ({r[1]})")
    else:
        print(f"{s}: ECHEC (ancien cours conservé)", file=sys.stderr)

OUT.write_text(json.dumps({"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                           "prices": prices}, indent=1))
sys.exit(0 if ok else 1)
