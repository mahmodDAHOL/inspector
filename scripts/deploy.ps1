$ErrorActionPreference = 'Stop'

$DeployHost = if ($env:DEPLOY_HOST) { $env:DEPLOY_HOST } else { 'inspector.momc.sy' }
$DeployUser = if ($env:DEPLOY_USER) { $env:DEPLOY_USER } else { 'ai-user' }
$DeployPath = if ($env:DEPLOY_PATH) { $env:DEPLOY_PATH } else { '/opt/inspection-portal' }
$WebRoot = if ($env:WEB_ROOT) { $env:WEB_ROOT } else { '/var/www/inspection-portal' }
$RemoteEnv = if ($env:REMOTE_ENV) { $env:REMOTE_ENV } else { '/etc/inspection-portal/backend.env' }
$Target = "$DeployUser@$DeployHost"
$Archive = Join-Path $env:TEMP "inspection-portal-deploy-$([guid]::NewGuid()).tar.gz"
$RemoteArchive = "/tmp/$(Split-Path $Archive -Leaf)"

try {
    if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) { throw 'OpenSSH client is required.' }
    if (-not (Get-Command scp -ErrorAction SilentlyContinue)) { throw 'scp is required.' }
    if (-not (Get-Command tar -ErrorAction SilentlyContinue)) { throw 'tar is required. Windows 10/11 normally includes it.' }
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm is required.' }

    Push-Location (Join-Path $PSScriptRoot '..')
    Write-Host 'Building frontend...'
    Push-Location (Join-Path (Get-Location) 'frontend')
    npm ci
    npm run build
    Pop-Location

    Write-Host 'Creating deployment archive...'
    tar -czf $Archive `
        --exclude='backend/__pycache__' `
        --exclude='backend/**/*.pyc' `
        --exclude='backend/.venv' `
        backend frontend/dist

    Write-Host 'Uploading deployment archive...'
    scp $Archive "${Target}:$RemoteArchive"

    Write-Host 'Installing release and restarting services...'
    $remoteCommand = @"
set -Eeuo pipefail
sudo mkdir -p '$DeployPath' '$WebRoot'
sudo tar -xzf '$RemoteArchive' -C '$DeployPath'
sudo rsync -a --delete '$DeployPath/frontend/dist/' '$WebRoot/'
sudo chown -R inspection:inspection '$DeployPath/backend'
sudo chown -R www-data:www-data '$WebRoot'
sudo -u inspection '$DeployPath/backend/.venv/bin/pip' install --quiet -r '$DeployPath/backend/requirements.txt'
sudo -u inspection bash -lc "cd '$DeployPath/backend'; set -a; . '$RemoteEnv'; set +a; .venv/bin/alembic upgrade head"
sudo systemctl restart inspection-backend
sudo systemctl is-active --quiet inspection-backend
curl --fail --silent --show-error -H 'Host: inspector.momc.sy' http://127.0.0.1:8000/health
echo
rm -f '$RemoteArchive'
"@
    $remoteCommand | ssh $Target 'bash -s'
    if ($LASTEXITCODE -ne 0) { throw "Remote deployment failed with exit code $LASTEXITCODE." }
    Write-Host "Deployment completed: https://$DeployHost/"
}
finally {
    Pop-Location -ErrorAction SilentlyContinue
    if (Test-Path $Archive) { Remove-Item -Force $Archive }
}