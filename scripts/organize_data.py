#!/usr/bin/env python3
"""Resumable corpus organization, separate from web startup."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.db import Session
from app.data_pipeline import run, VERSION
from app.models import Content
from sqlalchemy import update

p = argparse.ArgumentParser()
p.add_argument('--batch-size', type=int, default=500)
p.add_argument('--rebuild', action='store_true', help='Recalculer la projection relationnelle, sans modifier les sources.')
a = p.parse_args()
if not 1 <= a.batch_size <= 500: p.error('La taille des lots doit être entre 1 et 500.')
try:
    with Session() as s:
        if a.rebuild:
            s.execute(update(Content).values(structured_dirty=True)); s.commit()
        print('Organisation du corpus : ' + VERSION, flush=True)
        run(s, report=lambda message: print(message, flush=True), size=a.batch_size)
except KeyboardInterrupt:
    print('\nInterrompu : les lots terminés sont conservés. Relance la même commande pour reprendre.', flush=True)
    sys.exit(130)
