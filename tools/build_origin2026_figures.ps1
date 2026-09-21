param(
    [switch]$Mirror,
    [string[]]$Only = @()
)

$ErrorActionPreference = 'Stop'
$Invariant = [Globalization.CultureInfo]::InvariantCulture
$Runner = 'C:\Users\wishion\.codex\skills\origin-automation\scripts\run-origin-labtalk.ps1'
$DataRoot = Join-Path $PSScriptRoot '..\04_VASP_analysis\original_model_and_origin_delivery\figure_data_wide'
$DataRoot = [IO.Path]::GetFullPath($DataRoot)

function LTPath([string]$Path) {
    return $Path.Replace('\', '\\').Replace('"', '""')
}

function ColumnName([int]$Index) {
    $s = ''
    while ($Index -gt 0) {
        $Index--
        $s = ([char](65 + ($Index % 26))) + $s
        $Index = [math]::Floor($Index / 26)
    }
    return $s
}

function HeadersOf([string]$Path) {
    return @((Get-Content -LiteralPath $Path -TotalCount 1) -split ',' | ForEach-Object { $_.Trim('"') })
}

function CsvRows([string]$Path) {
    return @(Import-Csv -LiteralPath $Path)
}

function WriteSubset([string]$InputPath, [string]$OutputPath, [string[]]$Keep) {
    $rows = CsvRows $InputPath
    $rows | Select-Object -Property $Keep | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8
}

function WriteAggregate([string]$InputPath, [string]$OutputPath, [hashtable]$Groups) {
    $rows = CsvRows $InputPath
    $headers = HeadersOf $InputPath
    $x = $headers[0]
    $out = foreach ($row in $rows) {
        $obj = [ordered]@{ $x = $row.($x) }
        foreach ($name in $Groups.Keys) {
            $sum = 0.0
            $matched = $false
            foreach ($h in $Groups[$name]) {
                if ($row.PSObject.Properties.Name -contains $h) {
                    $sum += [double]::Parse([string]$row.($h), $Invariant)
                    $matched = $true
                }
            }
            if ($matched) { $obj[$name] = $sum.ToString('G17', $Invariant) }
        }
        [pscustomobject]$obj
    }
    $out | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8
}

function AddLabels([System.Collections.Generic.List[string]]$Commands, [string[]]$Headers) {
    for ($i = 0; $i -lt $Headers.Count; $i++) {
        $col = ColumnName ($i + 1)
        $label = $Headers[$i].Replace('_', ' ')
        $Commands.Add(('col({0})[L]$="{1}";' -f $col, $label))
    }
}

function ExportFormats([System.Collections.Generic.List[string]]$Commands, [int]$GraphIndex, [string]$Stem, [string]$FigureDir) {
    $page = "Graph$GraphIndex"
    $p = LTPath $FigureDir
    $Commands.Add(('expGraph type:=png overwrite:=replace export:=specified pages:="{0}" filename:="{1}" path:="{2}" tr1.unit:=0 tr1.width:=3.35 tr2.png.dotsperinch:=600;' -f $page, $Stem, $p))
    $Commands.Add(('expGraph type:=tif overwrite:=replace export:=specified pages:="{0}" filename:="{1}" path:="{2}" tr1.unit:=0 tr1.width:=3.35 tr2.tif.dotsperinch:=600;' -f $page, $Stem, $p))
    foreach ($kind in @('pdf', 'svg', 'eps')) {
        $Commands.Add(('expGraph type:={0} overwrite:=replace export:=specified pages:="{1}" filename:="{2}" path:="{3}";' -f $kind, $page, $Stem, $p))
    }
}

function AddLineGraph(
    [System.Collections.Generic.List[string]]$Commands,
    [ref]$GraphIndex,
    [string]$SourcePath,
    [string]$Stem,
    [string]$XLabel,
    [string]$YLabel,
    [string]$FigureDir
) {
    $headers = HeadersOf $SourcePath
    $escaped = LTPath $SourcePath
    $Commands.Add('newbook;')
    $Commands.Add(('impCSV fname:="{0}";' -f $escaped))
    AddLabels $Commands $headers
    $n = $headers.Count
    if ($n -eq 2) { $plot = 'plotxy iy:=(1,2) plot:=200;' }
    else { $plot = ('plotxy iy:=(1,2:{0}) plot:=200;' -f $n) }
    $Commands.Add($plot)
    $Commands.Add(('label -xb "{0}";' -f $XLabel))
    $Commands.Add(('label -yl "{0}";' -f $YLabel))
    $Commands.Add('layer.x.opposite=1; layer.y.opposite=1; rescale;')
    ExportFormats $Commands $GraphIndex.Value ([IO.Path]::GetFileNameWithoutExtension($Stem)) $FigureDir
    $GraphIndex.Value++
}

function AddGridGraph(
    [System.Collections.Generic.List[string]]$Commands,
    [ref]$GraphIndex,
    [string]$SourcePath,
    [string]$Stem,
    [string]$XLabel,
    [string]$YLabel,
    [string]$ZLabel,
    [double]$ZLimit,
    [string]$FigureDir
) {
    $escaped = LTPath $SourcePath
    $Commands.Add('newbook;')
    $Commands.Add(('impCSV fname:="{0}";' -f $escaped))
    $Commands.Add(('plotvm irng:=1! format:=xacross rowpos:=selrow1 colpos:=selcol1 ztitle:="{0}" type:=226 ogl:=<new template:=Contour>;' -f $ZLabel))
    $Commands.Add(('win -a Graph{0};' -f $GraphIndex.Value))
    $Commands.Add(('layer.cmap.zMin={0}; layer.cmap.zMax={1}; layer.cmap.numColors=21; layer.cmap.numMinorLevels=0; layer.cmap.SetLevels(1);' -f (-1.0 * $ZLimit), $ZLimit))
    $map = @(
        @(0,0,150), @(20,40,190), @(40,80,220), @(70,115,240), @(105,145,250),
        @(145,175,255), @(185,205,255), @(220,225,255), @(240,240,240), @(250,250,250),
        @(255,255,255), @(255,240,235), @(255,215,205), @(250,180,165), @(240,140,125),
        @(225,100,90), @(205,65,60), @(180,30,35), @(150,0,20), @(120,0,10), @(90,0,0)
    )
    for ($k = 0; $k -lt $map.Count; $k++) {
        $rgb = $map[$k]
        $Commands.Add(('layer.cmap.color{0}=color({1},{2},{3});' -f ($k + 1), $rgb[0], $rgb[1], $rgb[2]))
    }
    $Commands.Add('layer.cmap.updateScale();')
    $Commands.Add(('label -xb "{0}";' -f $XLabel))
    $Commands.Add(('label -yl "{0}";' -f $YLabel))
    $Commands.Add('layer.x.opposite=1; layer.y.opposite=1;')
    ExportFormats $Commands $GraphIndex.Value ([IO.Path]::GetFileNameWithoutExtension($Stem)) $FigureDir
    $GraphIndex.Value++
}

function RunOriginCategory([string]$CategoryDir, [string]$ProjectName, [System.Collections.Generic.List[string]]$Commands) {
    $cmdFile = Join-Path $CategoryDir ($ProjectName + '.ogs')
    $project = Join-Path $CategoryDir ($ProjectName + '.opju')
    $Commands | Set-Content -LiteralPath $cmdFile -Encoding ASCII
    & $Runner -NewProject -CommandFile $cmdFile -SaveAs $project | Out-Null
}

function MakeCategory([string]$Name, [scriptblock]$Builder) {
    if ($Only.Count -gt 0 -and $Only -notcontains $Name) { return }
    $dir = Join-Path $DataRoot $Name
    $figDir = Join-Path $dir 'figures_origin2026'
    $srcDir = Join-Path $figDir 'source_data'
    New-Item -ItemType Directory -Force -Path $figDir, $srcDir | Out-Null
    $commands = [System.Collections.Generic.List[string]]::new()
    $commands.Add('doc -mc 1;')
    $index = 1
    & $Builder $dir $figDir $srcDir $commands ([ref]$index)
    RunOriginCategory $dir ("origin2026_" + $Name) $commands
    return [pscustomobject]@{ Category = $Name; Graphs = ($index - 1); Project = (Join-Path $dir ("origin2026_" + $Name + '.opju')); FigureDir = $figDir }
}

function MakeGridCsv([string]$InputPath, [string]$OutputPath) {
    $rows = CsvRows $InputPath
    $xs = @($rows | ForEach-Object { [double]$_.x_A } | Sort-Object -Unique)
    $ys = @($rows | ForEach-Object { [double]$_.y_A } | Sort-Object -Unique)
    $lookup = @{}
    foreach ($r in $rows) { $lookup[('{0}|{1}' -f $r.x_A, $r.y_A)] = $r.value }
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add(('""' + (',' + (($xs | ForEach-Object { $_.ToString('G17', $Invariant) }) -join ','))))
    foreach ($y in $ys) {
        $vals = foreach ($x in $xs) {
            $key = '{0}|{1}' -f $x, $y
            if ($lookup.ContainsKey($key)) { $lookup[$key] } else { '0' }
        }
        $lines.Add((($y.ToString('G17', $Invariant)) + ',' + (($vals) -join ',')))
    }
    $lines | Set-Content -LiteralPath $OutputPath -Encoding UTF8
}

# Build density grids and a numeric Origin table for d/p centers.
$densityDir = Join-Path $DataRoot '06_difference_density_wide'
$densityGridDir = Join-Path $densityDir 'figures_origin2026\source_data'
New-Item -ItemType Directory -Force -Path $densityGridDir | Out-Null
$densityFields = @('charge_total_Al16','charge_total_undoped','magnetization_Al16','magnetization_undoped','spin_down_Al16','spin_down_undoped','spin_up_Al16','spin_up_undoped')
foreach ($field in $densityFields) {
    MakeGridCsv (Join-Path $densityDir ($field + '.csv')) (Join-Path $densityGridDir ($field + '_grid.csv'))
}

$centerDir = Join-Path $DataRoot '05_d_center_wide'
$centerInput = Join-Path $centerDir 'bare_system_d_p_center_width_weight_wide.csv'
$centerRows = CsvRows $centerInput
$centerPlot = Join-Path $centerDir 'figures_origin2026\source_data\d_center_plot_ready.csv'
New-Item -ItemType Directory -Force -Path (Split-Path $centerPlot) | Out-Null
$centerOut = foreach ($r in $centerRows) {
    [pscustomobject][ordered]@{
        model_index = if ($r.system -match 'Al16') { 1 } else { 2 }
        model = $r.system
        Co_d_occ_center_eV = $r.'Co_d_total_occupied_-8_0_center_relative_eV'
        Co_d_ext_center_eV = $r.'Co_d_total_extended_-8_4_center_relative_eV'
        O_p_occ_center_eV = $r.'O_p_total_occupied_-8_0_center_relative_eV'
        O_p_ext_center_eV = $r.'O_p_total_extended_-8_4_center_relative_eV'
        Co_d_occ_width_eV = $r.'Co_d_total_occupied_-8_0_width_eV'
        Co_d_ext_width_eV = $r.'Co_d_total_extended_-8_4_width_eV'
        O_p_occ_width_eV = $r.'O_p_total_occupied_-8_0_width_eV'
        O_p_ext_width_eV = $r.'O_p_total_extended_-8_4_width_eV'
        Co_d_occ_weight = $r.'Co_d_total_occupied_-8_0_integrated_weight'
        Co_d_ext_weight = $r.'Co_d_total_extended_-8_4_integrated_weight'
        O_p_occ_weight = $r.'O_p_total_occupied_-8_0_integrated_weight'
        O_p_ext_weight = $r.'O_p_total_extended_-8_4_integrated_weight'
        Fermi_level_eV = $r.fermi_level_eV
    }
}
$centerOut | Export-Csv -LiteralPath $centerPlot -NoTypeInformation -Encoding UTF8

$results = @()

$results += MakeCategory '01_system_pdos' {
    param($dir,$fig,$src,$cmd,[ref]$idx)
    $files = Get-ChildItem -LiteralPath $dir -Filter '*_system_wide_pdos.csv' | Sort-Object Name
    foreach ($f in $files) {
        $headers = HeadersOf $f.FullName
        $tdos = @($headers[0]) + @($headers | Where-Object { $_ -match '^TDOS_(up|down)$' })
        $tag = $f.BaseName -replace '_system_wide_pdos$',''
        $tdosSrc = Join-Path $src ($tag + '_TDOS.csv')
        WriteSubset $f.FullName $tdosSrc $tdos
        AddLineGraph $cmd $idx $tdosSrc ($tag + '_TDOS') 'E - EF (eV)' 'DOS (states/eV)' $fig
        $totals = @($headers[0]) + @($headers | Where-Object { $_ -match '^(Al|Co|O|H)_total_(up|down)$' })
        $totSrc = Join-Path $src ($tag + '_element_totals.csv')
        WriteSubset $f.FullName $totSrc $totals
        AddLineGraph $cmd $idx $totSrc ($tag + '_element_totals') 'E - EF (eV)' 'Projected DOS (states/eV)' $fig
    }
}

$results += MakeCategory '02_selected_pdos' {
    param($dir,$fig,$src,$cmd,[ref]$idx)
    $input = Join-Path $dir 'bare_selected_sites_wide.csv'
    $headers = HeadersOf $input
    $metal = @($headers[0]) + @($headers | Where-Object { $_ -match '^((Co|Al)\d+)_d_total_(up|down)$' })
    $oxygen = @($headers[0]) + @($headers | Where-Object { $_ -match '^O\d+_p_total_(up|down)$' })
    $metalSrc = Join-Path $src 'selected_metal_d_totals.csv'
    $oxygenSrc = Join-Path $src 'selected_oxygen_p_totals.csv'
    WriteSubset $input $metalSrc $metal
    WriteSubset $input $oxygenSrc $oxygen
    AddLineGraph $cmd $idx $metalSrc 'selected_metal_d_totals' 'E - EF (eV)' 'd-projected DOS (states/eV)' $fig
    AddLineGraph $cmd $idx $oxygenSrc 'selected_oxygen_p_totals' 'E - EF (eV)' 'p-projected DOS (states/eV)' $fig
}

$results += MakeCategory '03_formal_pdos_wide' {
    param($dir,$fig,$src,$cmd,[ref]$idx)
    foreach ($f in Get-ChildItem -LiteralPath $dir -Filter 'pdos_curves_*_wide.csv' | Sort-Object Name) {
        $rows = CsvRows $f.FullName
        $headers = HeadersOf $f.FullName
        $tag = $f.BaseName -replace '^pdos_curves_','' -replace '_wide$',''
        $groups = [ordered]@{}
        $groups['Co_d_up'] = @($headers | Where-Object { $_ -match '^Coact_\d+_d.*_up$' })
        $groups['Co_d_down'] = @($headers | Where-Object { $_ -match '^Coact_\d+_d.*_down$' })
        $groups['Oads_p_up'] = @($headers | Where-Object { $_ -match '^Oads_\d+_p.*_up$' })
        $groups['Oads_p_down'] = @($headers | Where-Object { $_ -match '^Oads_\d+_p.*_down$' })
        $groups['Obridge_p_up'] = @($headers | Where-Object { $_ -match '^Obridge_\d+_p.*_up$' })
        $groups['Obridge_p_down'] = @($headers | Where-Object { $_ -match '^Obridge_\d+_p.*_down$' })
        $groups = @{} + $groups
        $aggSrc = Join-Path $src ($tag + '_projected_summary.csv')
        WriteAggregate $f.FullName $aggSrc $groups
        AddLineGraph $cmd $idx $aggSrc ($tag + '_projected_summary') 'E - EF (eV)' 'Projected DOS (states/eV)' $fig
    }
}

$results += MakeCategory '04_formal_cohp_wide' {
    param($dir,$fig,$src,$cmd,[ref]$idx)
    foreach ($f in Get-ChildItem -LiteralPath $dir -Filter 'cohp_curves_*_minus_wide.csv' | Sort-Object Name) {
        $tag = $f.BaseName -replace '^cohp_curves_','' -replace '_minus_wide$',''
        $srcFile = Join-Path $src ($tag + '_minus_pCOHP.csv')
        $headers = HeadersOf $f.FullName
        WriteSubset $f.FullName $srcFile $headers
        AddLineGraph $cmd $idx $srcFile ($tag + '_minus_pCOHP') 'E - EF (eV)' '-pCOHP (eV)' $fig
    }
}

$results += MakeCategory '05_d_center_wide' {
    param($dir,$fig,$src,$cmd,[ref]$idx)
    $input = Join-Path $dir 'figures_origin2026\source_data\d_center_plot_ready.csv'
    $headers = HeadersOf $input
    $center = @($headers[0]) + @($headers | Where-Object { $_ -match 'center_eV$' })
    $width = @($headers[0]) + @($headers | Where-Object { $_ -match 'width_eV$' })
    $weight = @($headers[0]) + @($headers | Where-Object { $_ -match 'weight$' })
    $fermi = @($headers[0], 'Fermi_level_eV')
    $centerSrc = Join-Path $src 'd_p_centers.csv'
    $widthSrc = Join-Path $src 'd_p_widths.csv'
    $weightSrc = Join-Path $src 'd_p_weights.csv'
    $fermiSrc = Join-Path $src 'fermi_levels.csv'
    WriteSubset $input $centerSrc $center
    WriteSubset $input $widthSrc $width
    WriteSubset $input $weightSrc $weight
    WriteSubset $input $fermiSrc $fermi
    AddLineGraph $cmd $idx $centerSrc 'd_p_centers' 'Model (1 = Al16, 2 = undoped)' 'Center relative to EF (eV)' $fig
    AddLineGraph $cmd $idx $widthSrc 'd_p_widths' 'Model (1 = Al16, 2 = undoped)' 'Band width (eV)' $fig
    AddLineGraph $cmd $idx $weightSrc 'd_p_weights' 'Model (1 = Al16, 2 = undoped)' 'Integrated weight' $fig
    AddLineGraph $cmd $idx $fermiSrc 'fermi_levels' 'Model (1 = Al16, 2 = undoped)' 'Fermi level (eV)' $fig
}

$results += MakeCategory '06_difference_density_wide' {
    param($dir,$fig,$src,$cmd,[ref]$idx)
    $limits = @{}
    foreach ($pair in @(
        @('charge_total_Al16','charge_total_undoped'),
        @('magnetization_Al16','magnetization_undoped'),
        @('spin_down_Al16','spin_down_undoped'),
        @('spin_up_Al16','spin_up_undoped')
    )) {
        $all = foreach ($field in $pair) {
            CsvRows (Join-Path $dir ($field + '.csv')) | ForEach-Object { [math]::Abs([double]$_.value) }
        }
        $max = ($all | Measure-Object -Maximum).Maximum
        $lim = [math]::Ceiling($max * 1.02 * 1e8) / 1e8
        foreach ($field in $pair) { $limits[$field] = $lim }
    }
    foreach ($field in $densityFields) {
        $grid = Join-Path $dir ('figures_origin2026\source_data\' + $field + '_grid.csv')
        $safe = if ($limits[$field] -gt 0) { $limits[$field] } else { 1.0 }
        AddGridGraph $cmd $idx $grid ($field + '_heatmap') 'x (A)' 'y (A)' ($field -replace '_',' ') $safe $fig
    }
}

$manifest = Join-Path $DataRoot 'ORIGIN2026_FIGURE_MANIFEST.tsv'
$manifestRows = @("category`tgraphs`tproject`tfigure_dir")
foreach ($r in $results) { $manifestRows += ("{0}`t{1}`t{2}`t{3}" -f $r.Category, $r.Graphs, $r.Project, $r.FigureDir) }
$manifestRows | Set-Content -LiteralPath $manifest -Encoding UTF8

if ($Mirror) {
    $mirrorRoot = Join-Path $PSScriptRoot '..\staging\coooh_density_publish_20260915\04_VASP_analysis\rapid_delivery_package_20260920\figure_data_wide'
    $mirrorRoot = [IO.Path]::GetFullPath($mirrorRoot)
    if (Test-Path $mirrorRoot) {
        Copy-Item -LiteralPath (Join-Path $DataRoot 'ORIGIN2026_FIGURE_MANIFEST.tsv') -Destination $mirrorRoot -Force
        foreach ($cat in @('01_system_pdos','02_selected_pdos','03_formal_pdos_wide','04_formal_cohp_wide','05_d_center_wide','06_difference_density_wide')) {
            Copy-Item -LiteralPath (Join-Path $DataRoot $cat 'figures_origin2026') -Destination (Join-Path $mirrorRoot $cat) -Recurse -Force
        }
    }
}

$results | Format-Table -AutoSize
