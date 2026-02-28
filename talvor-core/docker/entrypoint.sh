#!/bin/sh
set -e

echo "Starting MATS backend..."

# --- Wait for database ---
echo "Waiting for database..."

until pg_isready -h db -U ats -d ats; do
  echo "Database not ready yet..."
  sleep 2
done

echo "Database is ready."

# --- Run migrations ---
echo "Running Alembic migrations..."
alembic upgrade head

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