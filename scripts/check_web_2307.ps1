$ErrorActionPreference = 'Stop'

$defaultRoute = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' |
    Sort-Object RouteMetric |
    Select-Object -First 1

$candidates = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.IPAddress -notlike '127.*' -and
        $_.IPAddress -notlike '169.254.*' -and
        $_.InterfaceAlias -notmatch 'VMware|VirtualBox|vEthernet|Loopback|Hyper-V'
    }

if ($defaultRoute) {
    $ip = $candidates |
        Where-Object { $_.InterfaceIndex -eq $defaultRoute.InterfaceIndex } |
        Select-Object -First 1 -ExpandProperty IPAddress
}

if (-not $ip) {
    $ip = $candidates | Select-Object -First 1 -ExpandProperty IPAddress
}

if (-not $ip) {
    throw 'No local IPv4 found.'
}

Write-Output "Using host: $ip"
Test-NetConnection -ComputerName $ip -Port 2307
