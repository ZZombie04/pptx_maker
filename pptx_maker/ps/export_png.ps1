param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [string]$OutDir = "",
  [int]$Width = 1600,
  [string]$Only = "",
  [string]$Measure = "",
  [string]$PidFile = ""
)
# PowerPoint 로 .pptx 를 열어(읽기 전용, 창 없이) 슬라이드를 PNG 로 내보내고, 글상자 실제 줄 수를 잰다.
# 사용자가 이미 띄운 PowerPoint 는 건드리지 않는다(이 스크립트가 띄운 경우에만 끈다).
$ErrorActionPreference = 'Stop'
function Get-OfficePids([string]$n) { @(Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object { $_.Id }) }
function Abs([string]$p) { if ([System.IO.Path]::IsPathRooted($p)) { return $p } return (Join-Path (Get-Location).Path $p) }
$Pptx = Abs $Pptx
if ($OutDir) { $OutDir = Abs $OutDir; New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }
$before = Get-OfficePids 'POWERPNT'
$pp = New-Object -ComObject PowerPoint.Application
$new = @(Get-OfficePids 'POWERPNT' | Where-Object { $before -notcontains $_ })
$ours = $new.Count -gt 0
if ($PidFile -and $ours) { [IO.File]::WriteAllText($PidFile, [string]$new[0]) }
$res = @{ slides = 0; exported = @(); measure = @() }
try {
  $pres = $pp.Presentations.Open($Pptx, -1, 0, 0)
  $ratio = $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth
  $sel = @()
  if ($Only) { $sel = $Only.Split(',') | ForEach-Object { [int]$_ } }
  $n = 0
  foreach ($sl in $pres.Slides) {
    $n++
    if ($sel.Count -gt 0 -and -not ($sel -contains $n)) { continue }
    if ($OutDir) {
      $f = Join-Path $OutDir ("s{0:D3}.png" -f $n)
      $sl.Export($f, 'PNG', $Width, [int]($Width * $ratio))
      $res.exported += $f
    }
    if ($Measure) {
      foreach ($sh in $sl.Shapes) {
        if (-not $sh.HasTextFrame) { continue }
        $tr = $sh.TextFrame2.TextRange
        $t = $tr.Text
        if (-not $t -or $t.Trim().Length -eq 0) { continue }
        $paras = $tr.Paragraphs().Count
        $brk = ($t.ToCharArray() | Where-Object { [int]$_ -eq 11 }).Count
        $lines = $tr.Lines().Count
        $m = $sh.TextFrame2
        $res.measure += @{ slide = $n; name = $sh.Name; lines = $lines; expected = $paras + $brk;
          boundH = [Math]::Round($tr.BoundHeight, 2); availH = [Math]::Round($sh.Height - $m.MarginTop - $m.MarginBottom, 2);
          text = $t.Substring(0, [Math]::Min(40, $t.Length)) }
      }
    }
  }
  $res.slides = $pres.Slides.Count
  $pres.Close()
}
finally {
  if ($ours) { $pp.Quit() }
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
}
if ($Measure) { [IO.File]::WriteAllText($Measure, ($res.measure | ConvertTo-Json -Depth 4 -Compress), (New-Object Text.UTF8Encoding $false)) }
"ok slides=$($res.slides) exported=$($res.exported.Count)"
