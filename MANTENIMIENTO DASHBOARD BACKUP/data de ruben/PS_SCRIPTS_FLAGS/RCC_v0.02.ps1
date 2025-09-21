#Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass


# INPUTS  --------------------------------------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------------------------------------------
# Path
# Configura la carpeta y el nombre de las columnas a analizar
$folderPath = "C:\RSA\MAINTENANCE\PROJECTS\TITAN\RCC\RCC RM2\20250804_JulyData\2025-07\2025-07\SampleFiles"

# Flags reales en los archivos
$flagsReales = @("OPTIBAT_ON", "MacroState_flag", "Support", "ResulExistance_Quality_flag", "OPTIBAT_COMMUNICATION")

# Flags virtuales
$flagsVirtuales = @("OPTIBAT_READY", "OPTIBAT_ON_OPTIBAT_READY", "OPTIBAT_OFF_OPTIBAT_READY")

# Lista completa de flags a analizar
$flagsAAnalizar = $flagsReales + $flagsVirtuales

# Inicializar acumuladores globales
$acumulado = @{}
foreach ($flag in $flagsAAnalizar) {
    $acumulado[$flag] = @{ Total = 0; Activos = 0 }
}

# Buscar todos los archivos .osf en la carpeta
$files = Get-ChildItem -Path $folderPath -Filter *.osf

foreach ($file in $files) {
    Write-Host "`nAnalizando archivo: $($file.Name)"
    
    $lines = Get-Content $file.FullName
    if ($lines.Count -lt 2) {
        Write-Host "Archivo vacío o con formato inesperado." -ForegroundColor Yellow
        continue
    }

    # Buscar cabecera (línea que empieza por "VarName")
    $headerLine = $lines | Where-Object { $_ -like "VarName*" }
    if (-not $headerLine) {
        Write-Host "No se encontró línea VarName en $($file.Name)" -ForegroundColor Red
        continue
    }

    $columns = $headerLine -split "`t"
    $dataLines = $lines | Where-Object { $_ -match '^\d' }

    # Obtener los índices de las columnas relevantes
    $indices = @{}
    foreach ($flag in $flagsReales) {
        $indices[$flag] = $columns.IndexOf($flag)
        if ($indices[$flag] -eq -1) {
            Write-Host "No se encontró la columna '$flag' en $($file.Name)" -ForegroundColor Red
        }
    }

    # Inicializar contadores por archivo
    $contadores = @{}
    foreach ($flag in $flagsAAnalizar) {
        $contadores[$flag] = @{ Total = 0; Activos = 0 }
    }

    # Procesar líneas de datos
    foreach ($line in $dataLines) {
        $parts = $line -split "`t"

        # Extraer valores de flags reales con conversión segura
        $valores = @{}
        foreach ($flag in $flagsReales) {
            $value = 0
            $idx = $indices[$flag]
            if ($idx -ge 0 -and $idx -lt $parts.Count) {
                $raw = $parts[$idx].Trim()

                #if ($raw -eq "" -or $raw -eq $null) {
                #    $value = 0
                #    } else {
                #    $parsed = 0
                #    if ([double]::TryParse($raw, [ref]$parsed)) {
                #        $value = $parsed
                #    } else {
                #        Write-Warning "Valor no numérico encontrado: '$raw' en archivo $($file.Name)"
                #        $value = 0
                #    }
                #}
                if ($raw -eq "" -or $raw -eq $null -or $raw -eq "null") {
                    $value = 0
                } else {
                    $parsed = 0
                    if ([double]::TryParse($raw, [ref]$parsed)) {
                        $value = $parsed
                    } else {
                        Write-Warning "Valor no numérico encontrado: '$raw' en archivo $($file.Name)"
                        $value = 0
                    }
                }
            }
            $valores[$flag] = $value

            # Contar activos reales
            $contadores[$flag].Total++
            if ($value -ne 0) { $contadores[$flag].Activos++ }
        }

        # Calcular OPTIBAT_READY
        $ready = if (
            $valores["ResulExistance_Quality_flag"] -eq 1 -and
            $valores["Support"] -eq 1 -and
            $valores["MacroState_flag"] -eq 1
        ) { 1 } else { 0 }

        $contadores["OPTIBAT_READY"].Total++
        if ($ready -eq 1) { $contadores["OPTIBAT_READY"].Activos++ }

        # Calcular OPTIBAT_ON_OPTIBAT_READY
        $onAndReady = if (
            $valores["OPTIBAT_ON"] -eq 1 -and $ready -eq 1
        ) { 1 } else { 0 }

        $contadores["OPTIBAT_ON_OPTIBAT_READY"].Total++
        if ($onAndReady -eq 1) { $contadores["OPTIBAT_ON_OPTIBAT_READY"].Activos++ }

        # Calcular OPTIBAT_OFF_OPTIBAT_READY
        $offAndReady = if (
            $valores["OPTIBAT_ON"] -eq 0 -and $ready -eq 1
        ) { 1 } else { 0 }

        $contadores["OPTIBAT_OFF_OPTIBAT_READY"].Total++
        if ($offAndReady -eq 1) { $contadores["OPTIBAT_OFF_OPTIBAT_READY"].Activos++ }
    }

    # Mostrar resultados por archivo
    foreach ($flag in $flagsAAnalizar) {
        $total = $contadores[$flag].Total
        $activos = $contadores[$flag].Activos
        $acumulado[$flag].Total += $total
        $acumulado[$flag].Activos += $activos

        if ($total -gt 0) {
            $porcentaje = [math]::Round(100 * $activos / $total, 2)
            Write-Host "${flag}: $porcentaje% activo ($activos de $total)"
        }
    }
}

# Mostrar resumen global
Write-Host "`n========== RESUMEN GLOBAL DE TODOS LOS ARCHIVOS ==========" -ForegroundColor Cyan
foreach ($flag in $flagsAAnalizar) {
    $total = $acumulado[$flag].Total
    $activos = $acumulado[$flag].Activos
    if ($total -gt 0) {
        $porcentaje = [math]::Round(100 * $activos / $total, 2)
        Write-Host "${flag}: $porcentaje% activo ($activos de $total)" -ForegroundColor Green
    } else {
        Write-Host "${flag}: Sin datos." -ForegroundColor Yellow
    }
}
