#!/usr/bin/env python3
"""Read public dataset metadata/card without importing or approving its contents.

Standard library only. Respects configured proxy and TLS trust. No token needed
for a public dataset; no login or credential discovery is attempted.
"""
import argparse
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

REPO='Sifal/Kabyle-French'
API='https://huggingface.co/api/datasets/'+REPO
ROOT=Path(__file__).resolve().parents[1]

def get(url,limit):
    request=urllib.request.Request(url,headers={'User-Agent':'Tifin-source-audit/0.1'})
    with urllib.request.urlopen(request,timeout=30) as response:
        raw=response.read(limit+1)
        if len(raw)>limit:raise ValueError('Metadata response exceeds the bounded audit size')
        return raw

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata-file',type=Path,help='Optional public API metadata previously downloaded from the dataset page')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/sifal-audit')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    report={'dataset':REPO,'url':'https://huggingface.co/datasets/'+REPO,'imported_rows':0,'approved_for_lessons':False}
    try:
        if args.metadata_file and args.metadata_file.stat().st_size>2*1024*1024: raise ValueError('Metadata file exceeds the bounded audit size')
        raw=args.metadata_file.read_bytes() if args.metadata_file else get(API,2*1024*1024)
        meta=json.loads(raw)
        if not isinstance(meta,dict) or meta.get('id')!=REPO:raise ValueError('Metadata is not for the requested dataset')
        (args.output/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        card=meta.get('cardData') or {}
        report.update(access='metadata_read',revision=meta.get('sha'),declared_license=card.get('license'),license_tags=[t for t in meta.get('tags',[]) if t.startswith('license:')],declared_languages=card.get('language'),gated=meta.get('gated'),files=[s.get('rfilename') for s in meta.get('siblings',[])])
        sha=meta.get('sha','')
        if re.fullmatch(r'[a-f0-9]{40}',sha):
            try:
                readme=get('https://huggingface.co/datasets/'+REPO+'/resolve/'+sha+'/README.md',1024*1024)
                (args.output/'README.md').write_bytes(readme)
                report['card']='README.md saved at immutable revision'
            except urllib.error.HTTPError as e:report['card']='not retrieved: HTTP '+str(e.code)
            except OSError:report['card']='not retrieved: network access unavailable'
        report['next_step']='Verify the actual license, provenance, columns, alignment, duplicates and suitability of selected examples before any import. An aligned sentence corpus is not automatically a word dictionary.'
        status=0
    except urllib.error.HTTPError as e:
        report.update(access='http_refused',http_status=e.code,next_step='The metadata could not be read. Check the network policy or retry from an authorized connection. No missing credential or license conclusion can be drawn from this response alone.')
        status=1
    except (OSError,ValueError,TypeError) as e:
        report.update(access='unavailable',error=str(e),next_step='No data imported; resolve the access or metadata issue first.')
        status=1
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return status

if __name__=='__main__':raise SystemExit(main())
