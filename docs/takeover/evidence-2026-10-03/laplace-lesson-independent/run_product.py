"""Post-freeze runner: actual HTTP or archived raw responses, never a fake handler."""
import argparse
from datetime import datetime,timezone
import hashlib
import http.client
import json
from pathlib import Path
import sys
import checker as C


def source_manifest(repo):
    files={str(p.relative_to(repo)):C.sha(p.read_bytes()) for p in sorted((repo/'src').rglob('*.py'))}
    return {'files':files,'manifest_sha256':C.sha(C.encoded(files))}


def run():
    parser=argparse.ArgumentParser()
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--port',type=int)
    source.add_argument('--responses',type=Path,help='JSONL from prior real HTTP run, retains original payloads')
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=args.output.resolve(); raw_path=output.with_suffix('.responses.jsonl')
    assert not output.exists() and not raw_path.exists(),'refusing to overwrite evidence'
    cases,criteria=C.integrity()
    before=source_manifest(args.repo.resolve())
    archived={}
    if args.responses:
        for line in args.responses.read_text().splitlines():
            row=json.loads(line); assert row['id'] not in archived
            archived[row['id']]=row
    started=datetime.now(timezone.utc).isoformat()
    rows=[]; raw=[]; blocked=None
    for entry in cases:
        try:
            if args.port:
                connection=http.client.HTTPConnection('127.0.0.1',args.port,timeout=180)
                request=C.encoded({'netlist':entry['netlist'],'method':'auto'})
                try:
                    connection.request('POST','/api/solve',request,{'Content-Type':'application/json'})
                    response=connection.getresponse()
                    body=response.read(64*1024*1024+1)
                    assert len(body)<=64*1024*1024,'response exceeded 64 MiB'
                    wire={'id':entry['id'],'status':response.status,'body':body.decode('utf-8'),
                        'body_sha256':C.sha(body),'body_bytes':len(body),'request_sha256':C.sha(request)}
                finally: connection.close()
            else:
                wire=archived[entry['id']]
                assert C.sha(wire['body'].encode())==wire['body_sha256'],'archived bytes changed'
            raw.append(wire)
            if wire['status']!=200:
                row={'id':entry['id'],'ok':False,'errors':[f"HTTP {wire['status']}"],
                    'response':json.loads(wire['body'])}
            else:
                payload=json.loads(wire['body'])
                row=C.compare_lesson(entry,payload)
                row['mutations']=[]
                if row['ok']:
                    kinds=['intermediate_equation_plus_one','initial_condition_sign']
                    if entry['id']=='mixed_impulses': kinds+=['impulse_area_unit']
                    for kind in kinds:
                        audit=C.compare_lesson(entry,C.mutated(payload,kind))
                        rejected=not audit['ok']
                        row['mutations'].append({'kind':kind,'rejected':rejected,'errors':audit['errors'][:8]})
                        if not rejected: row['ok']=False; row['errors'].append('mutation survived: '+kind)
            rows.append(row)
            print(json.dumps({'case':entry['id'],'ok':row['ok'],'equations':row.get('equations'),
                              'errors':row['errors'][:3]}),flush=True)
        except (OSError,AssertionError,KeyError,TypeError,ValueError) as exc:
            blocked=f'{type(exc).__name__}: {exc}'
            break
    after=source_manifest(args.repo.resolve())
    raw_path.write_text(''.join(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n' for row in raw))
    receipt={'schema':'independent-laplace-lesson-result.v1','started_at':started,
        'ended_at':datetime.now(timezone.utc).isoformat(),'model':'inherited/unknown',
        'criteria_sha256':C.sha((C.ROOT/'criteria.json').read_bytes()),
        'runner_sha256':C.sha(Path(__file__).read_bytes()),
        'transport':f'HTTP http://127.0.0.1:{args.port}/api/solve' if args.port else f'archived {args.responses}',
        'classification':criteria['classification'],'source_before':before,'source_after':after,
        'source_unchanged':before==after,'raw_sha256':C.sha(raw_path.read_bytes()),
        'blocked':blocked,'results':rows,
        'ok':blocked is None and len(rows)==len(cases) and all(r['ok'] for r in rows) and before==after,
        'limitations':criteria['limitations'],'index_sync':'INDEX_SYNC_DEFERRED'}
    output.write_bytes(C.encoded(receipt))
    print(json.dumps({'ok':receipt['ok'],'cases':len(rows),'blocked':blocked,'output':str(output)}))
    raise SystemExit(0 if receipt['ok'] else 1)

if __name__=='__main__': run()
