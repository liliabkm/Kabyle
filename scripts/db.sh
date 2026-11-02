#!/usr/bin/env bash
set -euo pipefail
# The development password is intentionally local-only. Bind no public port.
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
if docker --host=unix:///var/run/docker.sock container inspect kabyle-postgres >/dev/null 2>&1; then
  docker --host=unix:///var/run/docker.sock start kabyle-postgres >/dev/null
else
  docker --host=unix:///var/run/docker.sock run -d --name kabyle-postgres \
    -e POSTGRES_USER=kabyle -e POSTGRES_PASSWORD=kabyle_local -e POSTGRES_DB=kabyle \
    -p 127.0.0.1:5432:5432 -v kabyle-postgres-data:/var/lib/postgresql/data \
    postgres:17-alpine@sha256:266d3c257594e195b309ae9d1805e54c788f1d7b375f56bf6c367aac6c917e7b >/dev/null
fi
for i in {1..30}; do
  if docker --host=unix:///var/run/docker.sock exec kabyle-postgres pg_isready -U kabyle -d kabyle >/dev/null 2>&1; then exit 0; fi
  sleep 1
done
echo 'PostgreSQL not ready' >&2
exit 1
