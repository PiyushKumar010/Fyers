import requests

urls = [
    "http://localhost:8000/market/quote?symbol=NSE:NIFTY50-INDEX",
    "http://localhost:8000/market/quote?symbol=NSE:NIFTYBANK-INDEX",
    "http://localhost:8000/market/quote?symbol=BSE:SENSEX-INDEX",
    "http://localhost:8000/market/quotes?symbols=NSE:NIFTY50-INDEX,NSE:NIFTYBANK-INDEX,BSE:SENSEX-INDEX",
    "http://localhost:8000/api/trend/analyze?symbol=NSE:NIFTY50-INDEX",
    "http://localhost:8000/api/trend/stochastic?symbol=NSE:NIFTY50-INDEX",
]

lines = []

for url in urls:
    try:
        resp = requests.get(url)
        lines.append(f"--- {url}")
        lines.append(f"status {resp.status_code}")
        lines.append(resp.text[:800])
    except Exception as e:
        lines.append(f"--- {url} ERROR {e}")

output_path = "call_endpoints_output.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Wrote results to {output_path}")
