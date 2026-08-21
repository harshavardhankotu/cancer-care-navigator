#!/usr/bin/env bash
# Nightly backup of the database (health data = back it up like it matters).
# Install on the VPS:  crontab -e  →  0 3 * * * /opt/ccn/scripts/backup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
docker compose exec -T db pg_dump -U ccn ccn | gzip > "backups/ccn-$(date +%F).sql.gz"
find backups -name 'ccn-*.sql.gz' -mtime +14 -delete
echo "backup done: backups/ccn-$(date +%F).sql.gz"
