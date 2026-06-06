param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,

  [string]$OutputPath,
  [int]$Width = 8100,
  [int]$Height = 1080,
  [string]$Model = "prob-4",
  [ValidateSet("Crop", "Stretch", "Pad")]
  [string]$Fit = "Crop",
  [int]$Cq = 18
)

$ErrorActionPreference = "Stop"

$topazDir = "C:\Program Files\Topaz Labs LLC\Topaz Video"
$ffmpeg = Join-Path $topazDir "ffmpeg.exe"
$modelDir = "C:\ProgramData\Topaz Labs LLC\Topaz Video\models"

if (-not (Test-Path -LiteralPath $ffmpeg)) {
  throw "Topaz ffmpeg was not found at: $ffmpeg"
}

if (-not (Test-Path -LiteralPath $InputPath)) {
  throw "Input video was not found: $InputPath"
}

if (-not (Test-Path -LiteralPath $modelDir)) {
  throw "Topaz model folder was not found: $modelDir"
}

if (-not $OutputPath) {
  $inputItem = Get-Item -LiteralPath $InputPath
  $OutputPath = Join-Path $inputItem.DirectoryName "$($inputItem.BaseName)_topaz_${Width}x${Height}.mp4"
}

$env:TVAI_MODEL_DATA_DIR = $modelDir
$env:TVAI_MODEL_DIR = $modelDir

$topazFilter = "tvai_up=model=${Model}:h=${Height}:download=1:device=0:instances=0:estimate=8"

switch ($Fit) {
  "Crop" {
    $videoFilter = "${topazFilter},scale=w=${Width}:h=${Height}:flags=lanczos:force_original_aspect_ratio=increase,crop=${Width}:${Height}"
  }
  "Stretch" {
    $videoFilter = "${topazFilter},scale=${Width}:${Height}:flags=lanczos"
  }
  "Pad" {
    $videoFilter = "${topazFilter},scale=w=${Width}:h=${Height}:flags=lanczos:force_original_aspect_ratio=decrease,pad=${Width}:${Height}:-1:-1:color=black"
  }
}

Write-Host "Input:  $InputPath"
Write-Host "Output: $OutputPath"
Write-Host "Target: ${Width}x${Height}, model ${Model}, fit ${Fit}"

& $ffmpeg `
  -hide_banner -y `
  -i $InputPath `
  -map 0:v:0 -map "0:a?" `
  -vf $videoFilter `
  -c:v hevc_nvenc -preset p7 -tune hq -rc vbr -cq $Cq -b:v 0 -pix_fmt yuv420p -tag:v hvc1 `
  -c:a copy -movflags +faststart `
  $OutputPath

if ($LASTEXITCODE -ne 0) {
  throw "Topaz upscale failed with exit code $LASTEXITCODE"
}

Write-Host "Done: $OutputPath"
