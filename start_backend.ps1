$env:SETTLEIQ_DEMO_SECRET = 'SiMGOe7hrmLMe6SfYxjOcqrKq-6vxDf95r8-v1zcAtGUlV0ikGZKW-pLK8tu-mAD'
$env:SETTLEIQ_API_KEY = 'Dx37N3u6L7kA8Nq9BbQ9E47R1Yx623Zmf4ZRIcwhfQs'
$env:PYTHONPATH = 'C:\Users\nares\Workspace\settleiq\src'
$env:SETTLEIQ_DB_PATH = ':memory:'
$env:SETTLEIQ_RATE_LIMIT = '1000'
$env:SETTLEIQ_DEMO_SESSION_RATE_LIMIT = '100'

$uvicornArgs = @(
    'python'
    '-m'
    'uvicorn'
    'settleiq.api.app:app'
    '--host'
    '127.0.0.1'
    '--port'
    '8001'
)

$uvicornProcess = Start-Process -FilePath $uvicornArgs[0] -ArgumentList $uvicornArgs[1..$uvicornArgs.Length] -NoNewWindow -PassThru

$maxAttempts = 30
for ($i = 0; $i -lt $maxAttempts; $i++) {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8001/health' -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host 'Backend is ready'
            break
        }
    } catch {
        # ignore
    }
    Start-Sleep -Seconds 1
}
if ($i -ge $maxAttempts) {
    Write-Error 'Backend failed to become ready in time'
    $uvicornProcess | Stop-Process -Force
    exit 1
}