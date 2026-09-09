<#
.SYNOPSIS
  Link (or copy) every skill in this repo into ~\.claude\skills so Claude Code can load it.

.DESCRIPTION
  Claude Code discovers skills one folder deep under ~\.claude\skills. This repo keeps skills in
  skills\<Category>\...\<skill>\SKILL.md, so each skill gets a directory junction (default) or a copy
  (-Copy) at ~\.claude\skills\<skill>. Sub-agents shipped with the SEO suite are copied to
  ~\.claude\agents. Re-run after pulling to pick up new skills. Safe to re-run.

.PARAMETER Copy
  Copy folders instead of creating junctions. Use when junctions aren't wanted (edits then must be
  made in the repo and re-installed).

.PARAMETER Uninstall
  Remove junctions (or copies) that point at this repo, and the SEO agents it installed.
#>
param([switch]$Copy, [switch]$Uninstall)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$skillsHome = Join-Path $HOME '.claude\skills'
$agentsHome = Join-Path $HOME '.claude\agents'
New-Item -ItemType Directory -Force -Path $skillsHome, $agentsHome | Out-Null

# Skip runtime folders (the SEO suite's Python venv ships third-party SKILL.md files).
$skipNames = @('ms-playwright','node_modules','__pycache__','.git')
$skillDirs = Get-ChildItem -Path (Join-Path $repo 'skills') -Recurse -Filter SKILL.md -File |
  Where-Object { $segs = $_.FullName.Split('\'); -not ($segs | Where-Object { $_ -in $skipNames -or $_ -like '.venv*' }) } |
  ForEach-Object { $_.Directory } | Sort-Object Name -Unique

$agents = Get-ChildItem -Path (Join-Path $repo 'skills\SEO\claude-seo\agents') -Filter *.md -File -ErrorAction SilentlyContinue

if ($Uninstall) {
  foreach ($d in $skillDirs) {
    $target = Join-Path $skillsHome $d.Name
    if (Test-Path $target) {
      $item = Get-Item $target -Force
      if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { [IO.Directory]::Delete($target); Write-Host "unlinked $($d.Name)" }
      elseif ($Copy) { Remove-Item -Recurse -Force $target; Write-Host "removed copy $($d.Name)" }
      else { Write-Host "left $($d.Name) (real folder, not a junction; pass -Copy to remove copies)" }
    }
  }
  foreach ($a in $agents) { Remove-Item -Force (Join-Path $agentsHome $a.Name) -ErrorAction SilentlyContinue }
  Write-Host "Uninstall complete."
  return
}

$linked = 0; $skipped = 0
foreach ($d in $skillDirs) {
  $target = Join-Path $skillsHome $d.Name
  if (Test-Path $target) {
    $item = Get-Item $target -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
      $current = (Get-Item $target -Force).Target
      if ($current -eq $d.FullName) { $skipped++; continue }
      [IO.Directory]::Delete($target)
    } else {
      Write-Warning "skipping $($d.Name): a real folder already exists at $target"; $skipped++; continue
    }
  }
  if ($Copy) { Copy-Item -Recurse -Force $d.FullName $target }
  else { cmd /c mklink /J "`"$target`"" "`"$($d.FullName)`"" | Out-Null }
  $linked++
}
foreach ($a in $agents) { Copy-Item -Force $a.FullName (Join-Path $agentsHome $a.Name) }

Write-Host "Skills: $linked $(if ($Copy) {'copied'} else {'linked'}), $skipped already in place. Agents: $($agents.Count) copied."
Write-Host "SEO suite runtime: run  `"$skillsHome\seo\bin\claude-seo`" setup  once (creates an isolated Python environment)."
