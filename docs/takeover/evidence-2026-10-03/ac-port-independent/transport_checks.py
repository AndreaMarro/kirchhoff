"""Three frozen invalid inputs at the real loopback HTTP boundary; no retries."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8273)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists(): raise SystemExit('Refusing to overwrite previous evidence')
cases = json.loads((root/'cases.json').read_text())['cases']
rows, blocked = [], None
for case in cases:
    if case['id'] not in ['missing_port_terminal','same_port_terminal','zero_resistance_not_wire']: continue
    connection = http.client.HTTPConnection('127.0.0.1', args.port, timeout=30)
    try:
        body = json.dumps({'netlist':case['netlist'],'method':'test_current'}).encode()
        connection.request('POST','/api/solve',body,{'Content-Type':'application/json'})
        response = connection.getresponse()
        payload = response.read()
        data = json.loads(payload)
        rows.append({'case_id':case['id'],'status':response.status,'response':data,
                     'response_bytes':len(payload),'response_sha256':hashlib.sha256(payload).hexdigest(),
                     'passed':response.status == 422 and 'answer' not in data and bool(data.get('message'))})
    except OSError as error:
        blocked = f'{type(error).__name__}: {error}'
        break
    finally: connection.close()
result = {'scope':'post-opening HTTP boundary checks of three frozen invalid inputs',
          'endpoint':f'http://127.0.0.1:{args.port}/api/solve', 'blocked':blocked,
          'passed':blocked is None and len(rows) == 3 and all(row['passed'] for row in rows),'results':rows}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['passed'] else 1)
