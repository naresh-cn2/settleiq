$r = Invoke-WebRequest -Uri https://settleiq-zeta.vercel.app -Method Get -Headers @{ 'User-Agent'='Mozilla/5.0' } -UseBasicParsing -SkipCertificateCheck
$r.StatusCode