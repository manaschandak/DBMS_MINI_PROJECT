# Checks that the database can be built from nothing.
#
# It creates two scratch databases, builds the schema in one from the numbered SQL files and in
# the other from schema_snapshot.sql, compares both with battery_db, and drops the scratch
# databases again. battery_db itself is only read, never changed.
#
# Run from the project root, in a terminal where the password is already set:
#   $env:PGPASSWORD = "..."
#   powershell -NoProfile -ExecutionPolicy Bypass -File database\check_fresh_install.ps1

param([string]$User = "postgres")

$ErrorActionPreference = "Stop"

if (-not $env:PGPASSWORD) {
    throw 'Set the database password for this terminal first:  $env:PGPASSWORD = "..."'
}
if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\PostgreSQL\18\bin"
}
$env:PGOPTIONS = "-c client_min_messages=warning"

$dbDir = $PSScriptRoot

# The demo and experiment files are not part of the schema: 14 is an index experiment and
# 16 is a transaction demo that inserts sample readings.
$skip = @("14_index_experiment.sql", "16_transaction_demo.sql")
$steps = Get-ChildItem "$dbDir\*.sql" |
    Where-Object { $_.Name -match '^\d\d_' -and ($skip -notcontains $_.Name) } |
    Sort-Object Name

$countSql = "SELECT (SELECT count(*) FROM pg_tables WHERE schemaname = 'public'), " +
    "(SELECT count(*) FROM pg_views WHERE schemaname = 'public'), " +
    "(SELECT count(*) FROM information_schema.triggers WHERE trigger_schema = 'public'), " +
    "(SELECT count(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace), " +
    "(SELECT count(*) FROM pg_indexes WHERE schemaname = 'public')"

function Get-Counts($db) {
    $out = psql -U $User -d $db -t -A -F "," -c $countSql
    if ($LASTEXITCODE -ne 0) { throw "count query failed on $db" }
    return ($out | Out-String).Trim()
}

$fromFiles = "battery_fresh_files"
$fromSnapshot = "battery_fresh_snapshot"

$live = Get-Counts "battery_db"

try {
    foreach ($db in @($fromFiles, $fromSnapshot)) {
        psql -U $User -d postgres -q -c "DROP DATABASE IF EXISTS $db" -c "CREATE DATABASE $db"
        if ($LASTEXITCODE -ne 0) { throw "could not create scratch database $db" }
    }

    foreach ($f in $steps) {
        Write-Host ("running " + $f.Name)
        psql -U $User -d $fromFiles -q -v ON_ERROR_STOP=1 -f $f.FullName
        if ($LASTEXITCODE -ne 0) { throw ("FAILED in " + $f.Name) }
    }
    $countFiles = Get-Counts $fromFiles

    Write-Host "running schema_snapshot.sql"
    psql -U $User -d $fromSnapshot -q -v ON_ERROR_STOP=1 -f "$dbDir\schema_snapshot.sql"
    if ($LASTEXITCODE -eq 0) {
        $countSnap = Get-Counts $fromSnapshot
    } else {
        $countSnap = "snapshot FAILED (see the error above)"
    }

    Write-Host ""
    Write-Host "counts: tables,views,triggers,constraints,indexes"
    Write-Host ("battery_db (live)    : " + $live)
    Write-Host ("numbered SQL files   : " + $countFiles + $(if ($countFiles -eq $live) { "   MATCH" } else { "   DIFFERENT" }))
    Write-Host ("schema_snapshot.sql  : " + $countSnap + $(if ($countSnap -eq $live) { "   MATCH" } else { "   DIFFERENT" }))
}
finally {
    foreach ($db in @($fromFiles, $fromSnapshot)) {
        psql -U $User -d postgres -q -c "DROP DATABASE IF EXISTS $db"
    }
    Write-Host "scratch databases dropped"
}
