#!/usr/bin/env python3
"""Import the actual Sifal TSV, downloaded by the user, without retranslation."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.db import Session
from app.tsv_import import preview,import_file
p=argparse.ArgumentParser();p.add_argument('file',type=Path);p.add_argument('--kab-column',type=int);p.add_argument('--fr-column',type=int);p.add_argument('--has-header',action='store_true');p.add_argument('--preview',action='store_true');args=p.parse_args()
info=preview(args.file)
if args.preview:print(json.dumps(info,ensure_ascii=False,indent=2));sys.exit()
kab=args.kab_column or info['kab_column'];fr=args.fr_column or info['fr_column']
if not kab or not fr:p.error('Colonnes ambiguës : consulter --preview puis préciser --kab-column et --fr-column (à partir de 1).')
with Session() as s:print(json.dumps(import_file(s,args.file,kab,fr,args.has_header or info['has_header']),ensure_ascii=False,indent=2))
