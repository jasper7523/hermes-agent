Stop-Process -Name "Perplexity" -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

$AppPath = "C:\Users\promy\AppData\Local\Programs\Perplexity\Perplexity.exe"
Start-Process -FilePath $AppPath -ArgumentList "--remote-debugging-port=9222"

Write-Host "Perplexity App restarted with CDP (Port 9222) successfully." -ForegroundColor Green
