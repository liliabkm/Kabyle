#!/usr/bin/env python3
"""Local PostgreSQL snapshot + reproducibility manifest, never prints credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.db import engine

p = argparse.ArgumentParser()
p.add_argument('--container', help='Utiliser pg_dump dans ce conteneur PostgreSQL local.')
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
folder = root / 'artifacts/backups'
folder.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
output = folder / ('kabyle-' + stamp + '.dump')
if output.exists(): p.exit(1, 'Une sauvegarde de la même seconde existe déjà. Relance dans un instant.\n')
url = engine.url
env = os.environ.copy()
if a.container:
    command = ['docker','exec',a.container,'pg_dump','-U',url.username or 'kabyle','-d',url.database or 'kabyle','--format=custom','--no-owner','--no-acl']
elif shutil.which('pg_dump'):
    env.update(PGHOST=url.host or '127.0.0.1', PGPORT=str(url.port or 5432), PGUSER=url.username or 'kabyle', PGPASSWORD=url.password or '', PGDATABASE=url.database or 'kabyle')
    command = ['pg_dump','--format=custom','--no-owner','--no-acl']
else:
    p.exit(1, 'pg_dump absent. Pour le PostgreSQL Docker du projet : bash scripts/backup_data.sh --container kabyle-postgres\n')
partial = output.with_suffix('.partial')
try:
    fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as file:
        result = subprocess.run(command, env=env, stdout=file, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError('La sauvegarde PostgreSQL a échoué. Vérifie la disponibilité du serveur et la version de pg_dump.')
    partial.rename(output)
    h = hashlib.sha256()
    with output.open('rb') as file:
        for block in iter(lambda:file.read(1024 * 1024), b''): h.update(block)
    commit = subprocess.run(['git','rev-parse','HEAD'], cwd=root, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(['git','status','--porcelain'], cwd=root, capture_output=True, text=True).stdout.strip())
    manifest = {'worktree_dirty': dirty, 'created_at_utc':stamp, 'database_dump':output.name, 'sha256':h.hexdigest(), 'git_commit':commit,
        'note':'Inclut les contenus, corrections et progressions PostgreSQL. Les fichiers bruts, photos et audios distants doivent être conservés séparément.'}
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Sauvegarde créée : ' + str(output))
except (OSError, RuntimeError) as error:
    partial.unlink(missing_ok=True)
    p.exit(1, str(error)+'\n')
