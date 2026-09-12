$root = "04_VASP_analysis/electronic_structure_publication_data"
$names = @{
  "Al16__OH" = "Al16_OH"
  "Al16__O" = "Al16_O"
  "pristine__OH" = "pristine_OH"
  "pristine__O" = "pristine_O"
}

foreach ($kind in @("COHP", "PDOS")) {
  $stem = $kind.ToLower() + "_curves"
  $file = Join-Path $root "$kind/source_data/$stem.tsv"
  $header = Get-Content $file -TotalCount 1
  $rows = Import-Csv $file -Delimiter "`t"
  foreach ($key in $names.Keys) {
    $system = if ($key.StartsWith("Al16")) { "Al16" } else { "pristine" }
    $state = if ($key.EndsWith("__OH")) { "*OH" } else { "*O" }
    $out = Join-Path $root "$kind/source_data/$($stem)_$($names[$key]).tsv"
    $lines = @($header) + @(
      $rows | Where-Object { $_.system -eq $system -and $_.state -eq $state } |
        ForEach-Object {
          if ($kind -eq "COHP") {
            "{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}`t{7}`t{8}`t{9}`t{10}" -f $_.system,$_.state,$_.pair_role,$_.atom1_index,$_.atom2_index,$_.distance_A,$_.energy_eV_rel_EF,$_.spin,$_.pCOHP_raw,$_.minus_pCOHP,$_.source_file
          } else {
            "{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}`t{7}`t{8}`t{9}" -f $_.system,$_.state,$_.energy_eV_rel_EF,$_.spin,$_.site_role,$_.atom_index,$_.element,$_.orbital,$_.dos,$_.source_file
          }
        }
    )
    Set-Content -Path $out -Value $lines -Encoding utf8
  }
}

