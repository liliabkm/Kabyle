#!/usr/bin/env python3
import argparse,json,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.db import Session
from app.chat_dataset import export
p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,default=ROOT/'artifacts/chat-training'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
p.add_argument('--max-pairs',type=int)
a=p.parse_args()
if a.max_pairs is not None and a.max_pairs<1:p.error('--max-pairs doit être positif.')
print('Lecture du corpus et préparation des groupes…',flush=True)
with Session() as s:manifest=export(s,a.output,a.max_pairs,report=lambda text:print(text,flush=True))
manifest['code_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
(a.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=a.output.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(a.output.glob('*.json*')):z.write(path,path.name)
print(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Fichier à importer dans Colab : '+str(archive.resolve()),flush=True)
