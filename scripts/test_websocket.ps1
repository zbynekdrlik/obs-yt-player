# OBS WebSocket Test Script
# Tests connection to OBS WebSocket and retrieves scene information
#
# Usage: powershell -ExecutionPolicy Bypass -File test_websocket.ps1 [-Port 4459]

param(
    [int]$Port = 4455
)

function Send-OBSRequest {
    param(
        [System.Net.WebSockets.ClientWebSocket]$WebSocket,
        [string]$RequestType,
        [hashtable]$RequestData = @{},
        [string]$RequestId = "req_1"
    )

    $request = @{
        op = 6
        d = @{
            requestType = $RequestType
            requestId = $RequestId
            requestData = $RequestData
        }
    } | ConvertTo-Json -Depth 10 -Compress

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($request)
    $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$bytes)
    $WebSocket.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [System.Threading.CancellationToken]::None).Wait()

    $buffer = New-Object byte[] 8192
    $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$buffer)
    $result = $WebSocket.ReceiveAsync($segment, [System.Threading.CancellationToken]::None).Result
    $response = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $result.Count)
    return $response | ConvertFrom-Json
}

try {
    Write-Output "Testing OBS WebSocket on port $Port..."

    # Test TCP connection first
    $tcp = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    if (-not $tcp.TcpTestSucceeded) {
        Write-Output "FAILED: Port $Port is not listening"
        exit 1
    }
    Write-Output "OK: Port $Port is listening"

    # Connect WebSocket
    $ws = New-Object System.Net.WebSockets.ClientWebSocket
    $cts = New-Object System.Threading.CancellationTokenSource
    $cts.CancelAfter(10000)
    $ws.ConnectAsync([Uri]"ws://127.0.0.1:$Port", $cts.Token).Wait()
    Write-Output "OK: WebSocket connected"

    # Receive Hello
    $buffer = New-Object byte[] 4096
    $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$buffer)
    $result = $ws.ReceiveAsync($segment, [System.Threading.CancellationToken]::None).Result
    $hello = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $result.Count) | ConvertFrom-Json
    Write-Output "OK: Received Hello (OBS WebSocket v$($hello.d.obsWebSocketVersion))"

    # Send Identify (no auth)
    $identify = @{ op = 1; d = @{ rpcVersion = 1 } } | ConvertTo-Json -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($identify)
    $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$bytes)
    $ws.SendAsync($segment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [System.Threading.CancellationToken]::None).Wait()

    # Receive Identified
    $buffer = New-Object byte[] 4096
    $segment = New-Object System.ArraySegment[byte] -ArgumentList @(,$buffer)
    $result = $ws.ReceiveAsync($segment, [System.Threading.CancellationToken]::None).Result
    $identified = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $result.Count) | ConvertFrom-Json

    if ($identified.op -eq 2) {
        Write-Output "OK: Identified with OBS"
    } else {
        Write-Output "FAILED: Identification failed (may require authentication)"
        exit 1
    }

    # Get scene list
    $resp = Send-OBSRequest -WebSocket $ws -RequestType "GetSceneList" -RequestId "get_scenes"
    $currentScene = $resp.d.responseData.currentProgramSceneName
    $scenes = $resp.d.responseData.scenes.sceneName -join ", "
    Write-Output "Current scene: $currentScene"
    Write-Output "Available scenes: $scenes"

    # Get version
    $resp = Send-OBSRequest -WebSocket $ws -RequestType "GetVersion" -RequestId "get_version"
    Write-Output "OBS Version: $($resp.d.responseData.obsVersion)"
    Write-Output "Platform: $($resp.d.responseData.platform)"

    $ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "Test complete", [System.Threading.CancellationToken]::None).Wait()
    Write-Output ""
    Write-Output "SUCCESS: All WebSocket tests passed"

} catch {
    Write-Output "ERROR: $_"
    exit 1
}
