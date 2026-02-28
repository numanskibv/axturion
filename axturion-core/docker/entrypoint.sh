#!/bin/sh
set -e

echo "Starting Axturion Core..."

# Ensure relative paths (like alembic.ini, alembic/) resolve correctly.
cd /app

# --- Wait for database ---
echo "Waiting for database..."

# Derive connection params from DATABASE_URL to avoid hard-coding.
eval "$(python - <<'PY'
import os
import shlex
from urllib.parse import urlparse

url = os.environ.get('DATABASE_URL')
if not url:
    raise SystemExit('DATABASE_URL is not set')

u = urlparse(url)
host = u.hostname or 'db'
port = u.port or 5432
user = u.username or 'postgres'
dbname = (u.path or '').lstrip('/') or 'postgres'

print('PGHOST=' + shlex.quote(host))
print('PGPORT=' + shlex.quote(str(port)))
print('PGUSER=' + shlex.quote(user))
print('PGDATABASE=' + shlex.quote(dbname))
PY
)"

until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE"; do
  echo "Database not ready yet..."
  sleep 2
done

echo "Database is ready."

# --- Run migrations ---
echo "Running Alembic migrations..."
alembic -c alembic.ini upgrade head

# --- Optional seed ---
echo "Checking seed state..."

python - <<EOF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.domain.workflow.models import Workflow
import os

engine = create_engine(os.environ["DATABASE_URL"])
Session = sessionmaker(bind=engine)
db = Session()

if not db.query(Workflow).first():
    print("Seeding default workflow...")
    from app.core.seed import seed_workflow
    seed_workflow(db)
else:
    print("Seed already present.")

db.close()
EOF

echo "Starting API..."

exec "$@"