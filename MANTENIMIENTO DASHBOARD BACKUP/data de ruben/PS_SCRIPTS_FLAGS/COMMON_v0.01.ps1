#Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# INPUTS --------------------------------------------------------------------------------------------------------------------------------------------------------------
$basePath = "C:\RSA\MAINTENANCE\PROJECTS\CEMEX\FM1\20250701_JuneData"
$baseCode = "CEMEX"


# ABG #################################################################################################################################################################
if ($baseCode -eq "PAL" -or $baseCode -eq "DLL" -or $baseCode -eq "ABG") {
    $optibatOn = "OPTIBAT_ON"
    $optibatReady = "OPTIBAT_READY"
    $optibatResultExistance = "OPTIBAT_RESULTEXISTANCE"
    $optibatCommunication = "OPTIBAT_COMMUNICATION"
    $optibatSupport = "OPTIBAT_SUPPORT"
    $optibatMacrostates = "OPTIBAT_MACROSTATES"
    $optibatWatchdog = "OPTIBAT_WATCHDOG"


    $carpetas = @(
        @{ 
            Path = Join-Path $basePath "SampleFiles"; 
            Ext = "*.osf"; 
            Flags = @($optibatOn, $optibatReady, $optibatCommunication, $optibatResultExistance, $optibatSupport, $optibatMacrostates, $optibatWatchdog)
        },
        @{ 
            Path = Join-Path $basePath "Statistics"; 
            Ext = "*.txt"; 
            Flags = @()
        }
    )
}
# KSJ #################################################################################################################################################################
elseif ($baseCode -eq "KSJ") {
    $optibatOn = "OPTIBAT_ON"
    $optibatReady = "OPTIBAT_READY"
    $optibatResultExistance = "Resultexistance_Flag_Copy"
    $optibatCommunication = "OPTIBAT_COMMUNICATION"
    $optibatSupport = "Support_Flag_Copy"
    $optibatMacrostates = "Macrostates_Flag_Copy"
    $optibatWatchdog = "OPTIBAT_WATCHDOG"


    $carpetas = @(
        @{ 
            Path = Join-Path $basePath "SampleFiles"; 
            Ext = "*.osf"; 
            Flags = @($optibatOn, $optibatReady, $optibatCommunication, $optibatResultExistance, $optibatSupport, $optibatMacrostates, $optibatWatchdog)
        },
        @{ 
            Path = Join-Path $basePath "Statistics"; 
            Ext = "*.txt"; 
            Flags = @()
        }
    )
}
# MOL BCN  #############################################################################################################################################################
elseif ($baseCode -eq "BCN") {
    $optibatOn = "OPTIBAT_ON"
    $optibatReady = "OPTIBAT_READY"
    $optibatResultExistance = "ResultExistence_copy"
    $optibatCommunication = "KILN_OPTIBAT_COMMUNICATION"
    $optibatSupport = "Support_copy"
    $optibatMacrostates = "MacroState_copy"
    $optibatWatchdog = "OPTIBAT_WATCHDOG"


    $carpetas = @(
        @{ 
            Path = Join-Path $basePath "SampleFiles"; 
            Ext = "*.osf"; 
            Flags = @($optibatOn, $optibatReady, $optibatCommunication, $optibatWatchdog)
        },
        @{ 
            Path = Join-Path $basePath "Statistics"; 
            Ext = "*.txt"; 
            Flags = @($optibatMacrostates, $optibatResultExistance, $optibatSupport)
        }
    )
}
# MOL ALI  #############################################################################################################################################################
elseif ($baseCode -eq "ALI") {
    $optibatOn = "OPTIBAT_ON"
    $optibatReady = "OPTIBAT_READY"
    $optibatResultExistance = "Resultexistance_Flag_Copy"
    $optibatCommunication = "OPTIBAT_COMMUNICATION"
    $optibatSupport = "Support_Flag_Copy"
    $optibatMacrostates = "Macrostates_Flag_Copy"
    $optibatWatchdog = "OPTIBAT_WATCHDOG"


    $carpetas = @(
        @{ 
            Path = Join-Path $basePath "SampleFiles"; 
            Ext = "*.osf"; 
            Flags = @($optibatOn, $optibatReady, $optibatCommunication, $optibatWatchdog)
        },
        @{ 
            Path = Join-Path $basePath "Statistics"; 
            Ext = "*.txt"; 
            Flags = @($optibatMacrostates, $optibatResultExistance, $optibatSupport)
        }
    )
}
# CEMEX  #############################################################################################################################################################
elseif ($baseCode -eq "CEMEX") {
    $optibatOn = "OPTIBAT_ON"
    $optibatReady = "Flag_Ready"
    $optibatResultExistance = "Resultexistance_Flag_Copy"
    $optibatCommunication = "OPTIBAT_COMMUNICATION"
    $optibatSupport = "Support_Flag_Copy"
    $optibatMacrostates = "Macrostates_Flag_Copy"
    $optibatWatchdog = "OPTIBAT_WATCHDOG"


    $carpetas = @(
        @{ 
            Path = Join-Path $basePath "SampleFiles"; 
            Ext = "*.osf"; 
            Flags = @($optibatOn, $optibatReady, $optibatCommunication, $optibatWatchdog)
        },
        @{ 
            Path = Join-Path $basePath "Statistics"; 
            Ext = "*.txt"; 
            Flags = @($optibatMacrostates, $optibatResultExistance, $optibatSupport)
        }
    )
}
# ELSE #################################################################################################################################################################
else {
    $optibatOn = "OPTIBAT_ON"
    $optibatReady = "OPTIBAT_READY"
    $optibatCommunication = "OPTIBAT_COMMUNICATION"
    $optibatResultExistance = "OPTIBAT_RESULTEXISTANCE"
    $optibatCommunication = "OPTIBAT_COMMUNICATION"
    $optibatSupport = "OPTIBAT_SUPPORT"
    $optibatMacrostates = "OPTIBAT_MACROSTATES"
    $optibatWatchdog = "OPTIBAT_WATCHDOG"


    $carpetas = @(
        @{ 
            Path = Join-Path $basePath "SampleFiles"; 
            Ext = "*.osf"; 
            Flags = @($optibatOn, $optibatReady, $optibatCommunication, $optibatResultExistance, $optibatSupport, $optibatMacrostates, $optibatWatchdog)
        },
        @{ 
            Path = Join-Path $basePath "Statistics"; 
            Ext = "*.txt"; 
            Flags = @()
        }
    )

}


$flagVirtual = "OPTIBAT_ON_AND_READY"
$flagVirtual2 = "OPTIBAT_OFF_AND_READY"
$flagsVirtuales = @($flagVirtual, $flagVirtual2)

$flagsRealesTotales = $carpetas.Flags | ForEach-Object { $_ } | Select-Object -Unique
$flagsAAnalizar = $flagsRealesTotales + $flagsVirtuales
# ---------------------------------------------------------------------------------------------------------------------------------------------------------- FIN INPUTS



# SCRIPT --------------------------------------------------------------------------------------------------------------------------------------------------------------
$acumulado = @{}
foreach ($flag in $flagsAAnalizar) {
    $acumulado[$flag] = @{ Total = 0; Activos = 0 }
}


$lineasPorTiempo = @{}
$allSampleTimestamps = @()          # todos los timestamps (podrán contener duplicados)
$perFileInfo = @{}                  # info por fichero para desglose y debug

Write-Host "`n--- Procesando Estadísticas" -ForegroundColor Cyan


foreach ($carpeta in $carpetas) {
    $folderPath = $carpeta.Path
    $extension = $carpeta.Ext
    $flagsReales = $carpeta.Flags



    $files = Get-ChildItem -Path $folderPath -Filter $extension

    $totalFiles = $files.Count
    $counter = 0
    foreach ($file in $files) {
        #Write-Host "`nArchivo: $($file.FullName)"


        $counter++
        Write-Progress `
        -Activity "Procesando ficheros..." `
        -Status "Archivo $counter de ${totalFiles}: $($file.Name)" `
        -PercentComplete (($counter / $totalFiles) * 100)


        
        $lines = Get-Content $file.FullName
        if ($lines.Count -lt 2) {
            Write-Host "Archivo vacío o con formato inesperado." -ForegroundColor Yellow
            continue
        }

        $headerLine = $lines | Where-Object { $_ -like "VarName*" }
        if (-not $headerLine) {
            Write-Host "No se encontró línea VarName en $($file.Name)" -ForegroundColor Red
            continue
        }

        $columns = $headerLine -split "`t"
        $dataLines = $lines | Where-Object { $_ -match '^\d' }

        $indices = @{}
        foreach ($flag in $flagsReales) {
            $indices[$flag] = $columns.IndexOf($flag)
            if ($indices[$flag] -eq -1) {
                Write-Host "No se encontró la columna '$flag' en $($file.Name)" -ForegroundColor DarkYellow
            }
        }

         # COBERTURA MENSUAL ---------------------------------------------------------------------------------------
        $fileTimestamps = @()
        foreach ($line in $dataLines) {
            $parts = $line -split "`t"
            if ($parts.Count -gt 1) {
                $rawFecha = $parts[1].Trim()
                if ($rawFecha -ne "" -and $rawFecha -ne "null") {
                    try {
                        $dt = [datetime]::ParseExact($rawFecha, "yyyy-MM-dd HH:mm:ss", $null)
                        $fileTimestamps += $dt

                        # Solo acumular en cobertura mensual si el archivo está en SampleFiles
                        if ($file.DirectoryName -match "\\SampleFiles($|\\)") {
                            $allSampleTimestamps += $dt
                        }
                        #$allSampleTimestamps += $dt
                    } catch {
                        # si no parsea, ignoramos esa línea para el cálculo de cobertura
                    }
                }
            }
        }
        $perFileInfo[$file.Name] = @{
            TotalRows = $dataLines.Count
            TimestampsFound = $fileTimestamps.Count
            UniqueTimestamps = ($fileTimestamps | Sort-Object -Unique).Count
        }
        # ---------------------------------------------------------------------------------------------------------



        foreach ($line in $dataLines) {
            $parts = $line -split "`t"
            $timestamp = $parts[0].Trim()
            if (-not $lineasPorTiempo.ContainsKey($timestamp)) {
                $lineasPorTiempo[$timestamp] = @{}
            }

            foreach ($flag in $flagsReales) {
                $idx = $indices[$flag]
                $value = 0

                if ($idx -ge 0 -and $idx -lt $parts.Count) {
                    $raw = $parts[$idx].Trim()
                    if ($raw -eq $null -or $raw -eq "" -or $raw -eq "null") {
                        $parsed = 0
                    } else {
                        $success = [double]::TryParse($raw, [ref]$parsed)
                        if (-not $success) {
                            $parsed = 0
                        }
                    }
                    $value = $parsed
                }

                $lineasPorTiempo[$timestamp][$flag] = $value

                $acumulado[$flag].Total++
                if ($value -ne 0) { $acumulado[$flag].Activos++ }
            }
        }
    }
}

# FLAGS VIRTUALES ----------------------------------------------------------------------------
foreach ($timestamp in $lineasPorTiempo.Keys) {
    $valores = $lineasPorTiempo[$timestamp]

    if ($valores.ContainsKey($optibatOn) -and $valores.ContainsKey($optibatReady)) {
        $acumulado[$flagVirtual].Total++
        if ($valores[$optibatOn] -eq 1 -and $valores[$optibatReady] -eq 1) {
            $acumulado[$flagVirtual].Activos++
        }

        $acumulado[$flagVirtual2].Total++
        if ($valores[$optibatOn] -eq 0 -and $valores[$optibatReady] -eq 1) {
            $acumulado[$flagVirtual2].Activos++
        }
    }
}
#------------------------------------------------------------------------------------------------------------------------------------------------------------ FIN SCRIPT





# COB MENSUAL-----------------------------------------------------------------------------------------------------------------------------------------------------------
Write-Host "`n--- Calculando Cobertura Mensual" -ForegroundColor Cyan

if ($allSampleTimestamps.Count -gt 1) {

    # Unificamos y ordenamos timestamps
    $uniqueAll = $allSampleTimestamps | Sort-Object -Unique
    $countUnique = $uniqueAll.Count
    $totalIntervals = $countUnique - 1

    # Preparar intervalo y frecuencia de actualización para Write-Progress
    $intervals = @()
    if ($totalIntervals -le 0) { 
        Write-Host "`nNo hay intervalos a calcular (solo un timestamp único)." -ForegroundColor Yellow
    } else {
        # queremos ~100 actualizaciones como máximo -> calculamos cada cuántas iteraciones actualizar
        $updateEvery = [math]::Max(1, [int]([math]::Ceiling($totalIntervals / 100)))
        
        # Bucle pesado: calculo de intervalos consecutivos
        for ($i = 1; $i -lt $countUnique; $i++) {
            $d = ($uniqueAll[$i] - $uniqueAll[$i-1]).TotalSeconds
            if ($d -gt 0) {
                # redondeo a 6 decimales para agrupar pequeños ruidos
                $intervals += [math]::Round($d, 6)
            }

            # Actualizamos la barra cada $updateEvery iteraciones (o en la última)
            if ((($i % $updateEvery) -eq 0) -or ($i -eq $totalIntervals)) {
                $percent = [int](($i / $totalIntervals) * 100)
                Write-Progress -Id 1 `
                    -Activity "Calculando intervalos entre timestamps..." `
                    -Status "Intervalos calculados: $i de $totalIntervals" `
                    -PercentComplete $percent
            }
        }
        # completamos la barra de intervalos
        Write-Progress -Id 1 -Activity "Calculando intervalos entre timestamps..." -Completed

        if ($intervals.Count -gt 0) {
            # Mostrar un mensaje mientras calculamos el modo (puede costar si hay muchísimos elementos)
            Write-Progress -Id 2 -Activity "Agrupando intervalos y calculando modo..." -Status "Agrupando intervalos..." -PercentComplete 0
            $intervalMode = ($intervals | Group-Object | Sort-Object Count -Descending | Select-Object -First 1).Name
            $intervalSegundos = [double]$intervalMode
            Write-Progress -Id 2 -Activity "Agrupando intervalos y calculando modo..." -Completed

            # Determinamos el mes/año dominante entre timestamps (el que tiene más muestras)
            Write-Progress -Id 3 -Activity "Determinando mes/año dominante..." -Status "Agrupando por mes..." -PercentComplete 0
            $monthGroup = $uniqueAll | Group-Object { $_.ToString("yyyy-MM") } | Sort-Object Count -Descending | Select-Object -First 1
            Write-Progress -Id 3 -Activity "Determinando mes/año dominante..." -Completed

            $monthStr = $monthGroup.Name  # formato yyyy-MM
            $parts = $monthStr.Split("-")
            $yearDominante = [int]$parts[0]
            $monthDominante = [int]$parts[1]

            $diasMes = [DateTime]::DaysInMonth($yearDominante, $monthDominante)
            $muestrasEsperadas = ($diasMes * 24 * 3600) / $intervalSegundos

            # Conteo real: timestamps únicos que pertenecen al mes dominante
            $actualEnMes = ($uniqueAll | Where-Object { $_.ToString("yyyy-MM") -eq $monthStr }).Count

            $porcentajeCobertura = [math]::Round(100 * $actualEnMes / $muestrasEsperadas, 2)

            Write-Host "`n========== RESULTADO COBERTURA MES ==========" -ForegroundColor Magenta
            Write-Host "`Cobertura de mes en SampleFiles (mes dominante $monthStr): $porcentajeCobertura% ($actualEnMes de $([math]::Round($muestrasEsperadas,2)) muestras esperadas, intervalo usado: $intervalSegundos s)" -ForegroundColor GREEN

            # Desglose por fichero (útil para detectar solapamientos)
            #Write-Host "`nDesglose por fichero (filas totales / timestamps detectados / timestamps únicos en fichero):" -ForegroundColor DarkCyan

            $totalFiles = $perFileInfo.Keys.Count
            $counter = 0

            foreach ($k in $perFileInfo.Keys) {
                $counter++
                $percentFile = [int](($counter / $totalFiles) * 100)

                Write-Progress -Id 4 `
                    -Activity "Procesando ficheros para desglose" `
                    -Status "Fichero $counter de ${totalFiles}: $k" `
                    -PercentComplete $percentFile

                $info = $perFileInfo[$k]
                # Mostrar la info (puedes personalizar lo que quieras mostrar aquí)
                #Write-Host "$k : Rows=$($info.TotalRows) TimestampsFound=$($info.TimestampsFound) UniqueTimestamps=$($info.UniqueTimestamps)" -ForegroundColor Yellow
            }
            # completamos la barra del desglose
            Write-Progress -Id 4 -Activity "Procesando ficheros para desglose" -Completed
        } else {
            Write-Host "`nNo se pudieron calcular intervalos entre timestamps (no hay diferencias positivas)." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "`nNo se detectaron timestamps suficientes en SampleFiles para calcular cobertura." -ForegroundColor Yellow
}
#------------------------------------------------------------------------------------------------------------------------------------------------------------- FIN CALCCOB




# RESULTADO GLOBAL ----------------------------------------------------------------------------------------------------------------------------------------------------
Write-Host "`n========== RESUMEN GLOBAL DE FLAGS ==========" -ForegroundColor Magenta
foreach ($flag in $flagsAAnalizar) {
    $total = $acumulado[$flag].Total
    $activos = $acumulado[$flag].Activos

    if ($total -gt 0) {
        $porcentajeActivo = [math]::Round(100 * $activos / $total, 2)
        # Cálculo % respecto al mes completo
        $porcentajeMesCompleto = if ($muestrasEsperadas -gt 0) {
            [math]::Round(100 * $activos / $muestrasEsperadas, 2)
        } else {
            0
        }

        Write-Host "${flag}: $porcentajeActivo% activo ($activos de $total) | $porcentajeMesCompleto% respecto al mes completo" -ForegroundColor Green
    }
    else {
        Write-Host "${flag}: Sin datos." -ForegroundColor Yellow
    }
}
#------------------------------------------------------------------------------------------------------------------------------------------------------------- FIN RESULTADO
