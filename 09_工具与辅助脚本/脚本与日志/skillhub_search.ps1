$log = "C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\skillhub_search.txt"
$out = @()
$lm = "$env:USERPROFILE\.workbuddy\skills-marketplace\skills"
$out += "=== LOCAL MARKETPLACE: $lm ==="
if (Test-Path $lm) {
  Get-ChildItem $lm | ForEach-Object { $out += $_.Name }
} else {
  $out += "(not present)"
}
foreach ($q in @("batch download academic paper PDF","paper download","scihub","arxiv pdf download")) {
  try {
    $u = "https://lightmake.site/api/v1/search?q=" + [System.Uri]::EscapeDataString($q) + "&limit=10"
    $r = Invoke-RestMethod -Uri $u -TimeoutSec 25
    $out += ""
    $out += ("=== QUERY: " + $q + " ===")
    if ($r.results) {
      foreach ($item in $r.results) {
        $desc = $item.description_zh
        if (-not $desc) { $desc = $item.description }
        $out += ("- score=" + $item.score + " slug=" + $item.slug + " name=" + $item.displayName + " | dl=" + $item.downloads + " inst=" + $item.installs + " stars=" + $item.stars)
        $out += ("   " + $desc)
      }
    } else {
      $raw = $r | ConvertTo-Json -Compress
      if ($raw.Length -gt 300) { $raw = $raw.Substring(0,300) }
      $out += ("(no results) raw: " + $raw)
    }
  } catch {
    $out += ("ERR " + $q + " : " + $_.Exception.Message)
  }
}
$out | Out-File -FilePath $log -Encoding utf8
Write-Output "SEARCH-DONE"
