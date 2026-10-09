"""Récupère le dernier cours de clôture de chaque ligne de tickers.txt -> prices.json
Une ligne = un symbole Yahoo (ex. CS.PA) ou un ISIN (résolu automatiquement, cotation en EUR)."""
import json, re, sys, time, datetime, pathlib, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "prices.json"
ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
UA = {"User-Agent": "Mozilla/5.0"}

def get_json(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"  {url[-40:]} essai {i+1}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"  {url[-40:]} essai {i+1}: {e}", file=sys.stderr)
        time.sleep(3 * (i + 1))
    return None

def chart(sym):
    d = get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d")
    try:
        res = d["chart"]["result"][0]
        cur = res["meta"].get("currency")
        for ts, c in reversed(list(zip(res["timestamp"], res["indicators"]["quote"][0]["close"]))):
            if c is not None:
                day = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).date().isoformat()
                return round(c, 4), day, cur
    except Exception:
        pass
    return None

def candidates(isin):
    d = get_json(f"https://query1.finance.yahoo.com/v1/finance/search?q={isin}&quotesCount=8&newsCount=0")
    try:
        return [q["symbol"] for q in d["quotes"]]
    except Exception:
        return []

def fetch(key):
    syms = candidates(key) if ISIN.match(key) else [key]
    for s in syms:
        r = chart(s)
        if r and (not ISIN.match(key) or r[2] == "EUR"):
            return {"p": r[0], "d": r[1], "s": s}
    return None

def main():
    keys = [l.split("#")[0].strip() for l in (ROOT / "tickers.txt").read_text().splitlines()]
    keys = [k for k in keys if k]
    prices = json.loads(OUT.read_text()).get("prices", {}) if OUT.exists() else {}
    ok = 0
    for k in keys:
        r = fetch(k)
        if r:
            prices[k] = r; ok += 1
            print(f"{k}: {r['p']} ({r['d']}) via {r['s']}")
        else:
            print(f"{k}: ECHEC (ancien cours conservé)", file=sys.stderr)
    OUT.write_text(json.dumps({"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                               "prices": prices}, indent=1))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
