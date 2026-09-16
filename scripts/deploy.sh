#!/usr/bin/env bash
set -Eeuo pipefail

DEPLOY_HOST="${DEPLOY_HOST:-inspector.momc.sy}"
DEPLOY_USER="${DEPLOY_USER:-ai-user}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/inspection-portal}"
WEB_ROOT="${WEB_ROOT:-/var/www/inspection-portal}"
BACKEND_SERVICE="${BACKEND_SERVICE:-inspection-backend}"
REMOTE_ENV="${REMOTE_ENV:-/etc/inspection-portal/backend.env}"
TARGET="${DEPLOY_USER}@${DEPLOY_HOST}"
REMOTE_TMP="/tmp/inspection-portal-deploy-${USER}-${RANDOM}"

cleanup() {
  ssh "$TARGET" "rm -rf '$REMOTE_TMP'" >/dev/null 2>&1 || true
}
trap cleanup EXIT

command -v ssh >/dev/null || { echo "ssh is required" >&2; exit 1; }
command -v rsync >/dev/null || { echo "rsync is required" >&2; exit 1; }
command -v npm >/dev/null || { echo "npm is required" >&2; exit 1; }

echo "Building frontend..."
(cd frontend && npm ci && npm run build)

echo "Checking backend Python syntax..."
python3 -m compileall -q backend/app backend/scripts

echo "Preparing remote staging directory..."
ssh "$TARGET" "mkdir -p '$REMOTE_TMP/backend' '$REMOTE_TMP/frontend'"

echo "Uploading backend..."
rsync -az --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.venv/' \
  backend/ "$TARGET:$REMOTE_TMP/backend/"

echo "Uploading frontend build..."
rsync -az --delete frontend/dist/ "$TARGET:$REMOTE_TMP/frontend/"

echo "Installing release and restarting services..."
ssh "$TARGET" "
  set -Eeuo pipefail
  sudo mkdir -p '$DEPLOY_PATH/backend' '$WEB_ROOT'
  sudo rsync -a '$REMOTE_TMP/backend/' '$DEPLOY_PATH/backend/'
  sudo rsync -a --delete '$REMOTE_TMP/frontend/' '$WEB_ROOT/'
  sudo chown -R inspection:inspection '$DEPLOY_PATH/backend'
  sudo chown -R www-data:www-data '$WEB_ROOT'
  sudo -u inspection '$DEPLOY_PATH/backend/.venv/bin/pip' install --quiet -r '$DEPLOY_PATH/backend/requirements.txt'
  sudo -u inspection bash -lc "cd '$DEPLOY_PATH/backend'; set -a; . '$REMOTE_ENV'; set +a; .venv/bin/alembic upgrade head"
  sudo systemctl restart '$BACKEND_SERVICE'
  sudo systemctl is-active --quiet '$BACKEND_SERVICE'
  curl --fail --silent --show-error -H 'Host: inspector.momc.sy' http://127.0.0.1:8000/health
  echo
"

echo "Deployment completed: https://$DEPLOY_HOST/"