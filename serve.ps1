param(
    [int]$Port = 8000,
    [string]$Root = (Get-Location).Path
)

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()

Write-Host "Serving $Root at http://localhost:$Port/"

function Get-ContentType([string]$Path) {
    switch ([System.IO.Path]::GetExtension($Path).ToLowerInvariant()) {
        ".html" { "text/html; charset=utf-8" }
        ".css" { "text/css; charset=utf-8" }
        ".js" { "application/javascript; charset=utf-8" }
        ".json" { "application/json; charset=utf-8" }
        ".jpg" { "image/jpeg" }
        ".jpeg" { "image/jpeg" }
        ".png" { "image/png" }
        ".gif" { "image/gif" }
        ".webp" { "image/webp" }
        ".svg" { "image/svg+xml" }
        ".mp4" { "video/mp4" }
        default { "application/octet-stream" }
    }
}

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        $rawPath = $request.Url.AbsolutePath
        if ([string]::IsNullOrWhiteSpace($rawPath) -or $rawPath -eq "/") {
            $rawPath = "/index.html"
        }

        $relative = [System.Uri]::UnescapeDataString($rawPath.TrimStart("/"))
        $relative = $relative -replace "/", "\"
        $filePath = Join-Path $Root $relative

        if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
            $response.StatusCode = 404
            $bytes = [System.Text.Encoding]::UTF8.GetBytes("Not found")
            $response.ContentType = "text/plain; charset=utf-8"
            $response.OutputStream.Write($bytes, 0, $bytes.Length)
            $response.OutputStream.Close()
            continue
        }

        $fileInfo = Get-Item -LiteralPath $filePath
        $contentType = Get-ContentType $filePath
        $response.ContentType = $contentType
        $response.AddHeader("Accept-Ranges", "bytes")

        $rangeHeader = $request.Headers["Range"]
        $start = 0L
        $end = $fileInfo.Length - 1
        $isPartial = $false

        if ($rangeHeader -and $rangeHeader -match "^bytes=(\d*)-(\d*)$") {
            $isPartial = $true
            $startText = $Matches[1]
            $endText = $Matches[2]

            if ($startText -ne "") {
                $start = [Int64]$startText
            }
            if ($endText -ne "") {
                $end = [Int64]$endText
            }

            if ($start -gt $end -or $start -ge $fileInfo.Length) {
                $response.StatusCode = 416
                $response.AddHeader("Content-Range", "bytes */$($fileInfo.Length)")
                $response.OutputStream.Close()
                continue
            }

            if ($end -ge $fileInfo.Length) {
                $end = $fileInfo.Length - 1
            }
        }

        $length = ($end - $start) + 1
        if ($isPartial) {
            $response.StatusCode = 206
            $response.AddHeader("Content-Range", "bytes $start-$end/$($fileInfo.Length)")
        } else {
            $response.StatusCode = 200
        }

        $response.ContentLength64 = $length

        $fs = [System.IO.File]::Open($filePath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $fs.Seek($start, [System.IO.SeekOrigin]::Begin) | Out-Null
            $buffer = New-Object byte[] 65536
            $remaining = $length
            while ($remaining -gt 0) {
                $toRead = [int][Math]::Min($buffer.Length, $remaining)
                $read = $fs.Read($buffer, 0, $toRead)
                if ($read -le 0) { break }
                $response.OutputStream.Write($buffer, 0, $read)
                $remaining -= $read
            }
        } finally {
            $fs.Close()
        }

        $response.OutputStream.Close()
    }
} finally {
    if ($listener.IsListening) {
        $listener.Stop()
    }
    $listener.Close()
}

