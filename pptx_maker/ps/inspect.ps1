param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [string]$Out = "",
  [string]$Video = "",
  [int]$VideoHeight = 720,
  [int]$Fps = 30,
  [int]$SlideSec = 3,
  [string]$Pdf = "",
  [string]$PidFile = ""
)
# PowerPoint 로 .pptx 를 열어(읽기 전용, 창 없이) 장마다 전환·애니메이션 수를 읽고, 원하면 PDF·동영상(MP4)으로 내보낸다.
# 사용자가 이미 띄운 PowerPoint 는 건드리지 않는다(이 스크립트가 띄운 경우에만 끈다).
$ErrorActionPreference = 'Stop'
function Get-OfficePids([string]$n) { @(Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object { $_.Id }) }
$before = Get-OfficePids 'POWERPNT'
$pp = New-Object -ComObject PowerPoint.Application
$new = @(Get-OfficePids 'POWERPNT' | Where-Object { $before -notcontains $_ })
$ours = $new.Count -gt 0
if ($PidFile -and $ours) { [IO.File]::WriteAllText($PidFile, [string]$new[0]) }
$res = @{ slides = @(); video = ""; pdf = "" }
try {
  $pres = $pp.Presentations.Open($Pptx, -1, 0, 0)
  foreach ($sl in $pres.Slides) {
    $t = $sl.SlideShowTransition
    $res.slides += @{ n = $sl.SlideIndex; effect = $t.EntryEffect; dur = $t.Duration; anims = $sl.TimeLine.MainSequence.Count;
      advance = $t.AdvanceOnTime; shapes = $sl.Shapes.Count }
  }
  if ($Pdf) { $pres.SaveAs($Pdf, 32); $res.pdf = $Pdf }
  if ($Video) {
    $pres.CreateVideo($Video, $false, $SlideSec, $VideoHeight, $Fps, 85)
    $deadline = (Get-Date).AddMinutes(20)
    while ($pres.CreateVideoStatus -eq 1 -or $pres.CreateVideoStatus -eq 2) {
      if ((Get-Date) -gt $deadline) { break }
      Start-Sleep -Milliseconds 500
    }
    $res.video = "status=" + $pres.CreateVideoStatus
  }
  $pres.Close()
}
finally {
  if ($ours) { $pp.Quit() }
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
}
$json = $res | ConvertTo-Json -Depth 5 -Compress
if ($Out) { [IO.File]::WriteAllText($Out, $json, (New-Object Text.UTF8Encoding $false)) } else { $json }
