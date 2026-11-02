"""Import a reviewed JSON batch through the authenticated API, without printing secrets."""
import argparse, json, os, urllib.request
p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--base-url',default='http://127.0.0.1:8000');args=p.parse_args()
token=os.getenv('ADMIN_TOKEN')
if not token: p.error('Set ADMIN_TOKEN securely in the process environment')
with open(args.file) as f: data=json.load(f)
if not isinstance(data,list): p.error('Expected a JSON list')
req=urllib.request.Request(args.base_url+'/api/admin/import',data=json.dumps(data).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+token},method='POST')
with urllib.request.urlopen(req) as res: print(res.read().decode())
