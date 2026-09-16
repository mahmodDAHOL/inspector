# Deploy From Local PC

This project can be deployed to the native Linux installation without Docker.
The deployment scripts build the Vue frontend locally, upload the backend and
frontend build over SSH, run migrations, restart FastAPI, and check health.

## Server prerequisites

The server must already have:

- SSH access for the deployment user
- `/opt/inspection-portal/backend/.venv`
- `/etc/inspection-portal/backend.env`
- PostgreSQL and Redis running
- Nginx serving `/var/www/inspection-portal`
- The `inspection-backend` systemd service
- `rsync` installed on the server

The server environment file and TLS keys are never copied by these scripts.

## Windows PowerShell

Windows 10/11 normally includes OpenSSH (`ssh`, `scp`) and `tar`. If they are
missing, install **OpenSSH Client** from Windows Optional Features.

From the repository directory in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
$env:DEPLOY_HOST = 'inspector.momc.sy'
$env:DEPLOY_USER = 'ai-user'
$env:DEPLOY_PATH = '/opt/inspection-portal'
$env:WEB_ROOT = '/var/www/inspection-portal'
.\scripts\deploy.ps1
```

The PowerShell script runs `npm ci`, builds the frontend, creates a temporary
archive, uploads it with `scp`, then performs the server-side deployment.

## Bash or WSL

From the repository root:

```bash
chmod +x scripts/deploy.sh
export DEPLOY_HOST=inspector.momc.sy
export DEPLOY_USER=ai-user
export DEPLOY_PATH=/opt/inspection-portal
export WEB_ROOT=/var/www/inspection-portal
./scripts/deploy.sh
```

Both scripts may ask for the SSH password and sudo password on the server.
They do not print or copy application passwords, database credentials, Redis
credentials, or TLS private keys.

## Verify

```bash
curl -fsS https://inspector.momc.sy/health
sudo systemctl status inspection-backend --no-pager
```

For a rollback, restore the previous Git revision locally and run the script
again. Database migrations are forward-only, so review new migration files
before deploying a release that changes the schema.
