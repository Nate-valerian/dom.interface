param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,

  [string]$OutputPath,
  [int]$Width = 0,
  [int]$Height = 0,
  [double]$Scale = 4.0,
  [string]$Model = "prob-4",
  [ValidateSet("Crop", "Stretch", "Pad")]
  [string]$Fit = "Stretch",
  [int]$JpegQuality = 2
)

$ErrorActionPreference = "Stop"

$topazDir = "C:\Program Files\Topaz Labs LLC\Topaz Video"
$ffmpeg = Join-Path $topazDir "ffmpeg.exe"
$ffprobe = Join-Path $topazDir "ffprobe.exe"
$modelDir = "C:\ProgramData\Topaz Labs LLC\Topaz Video\models"

if (-not (Test-Path -LiteralPath $ffmpeg)) {
  throw "Topaz ffmpeg was not found at: $ffmpeg"
}

if (-not (Test-Path -LiteralPath $ffprobe)) {
  throw "Topaz ffprobe was not found at: $ffprobe"
}

if (-not (Test-Path -LiteralPath $InputPath)) {
  throw "Input image was not found: $InputPath"
}

if (-not (Test-Path -LiteralPath $modelDir)) {
  throw "Topaz model folder was not found: $modelDir"
}

if ($Scale -le 0) {
  throw "Scale must be greater than 0."
}

if ($Width -lt 0 -or $Height -lt 0) {
  throw "Width and Height must be 0 or greater."
}

if ($JpegQuality -lt 1 -or $JpegQuality -gt 31) {
  throw "JpegQuality must be between 1 and 31. Lower is better quality."
}

$inputItem = Get-Item -LiteralPath $InputPath
$supportedInput = @(".png", ".tif", ".tiff", ".jpg", ".jpeg", ".webp", ".bmp")
if ($supportedInput -notcontains $inputItem.Extension.ToLowerInvariant()) {
  throw "Unsupported input image extension '$($inputItem.Extension)'. Supported: $($supportedInput -join ', ')"
}

$probeJson = & $ffprobe `
  -v error `
  -select_streams v:0 `
  -show_entries stream=width,height `
  -of json `
  $InputPath

if ($LASTEXITCODE -ne 0) {
  throw "Could not read image dimensions with ffprobe."
}

$probe = $probeJson | ConvertFrom-Json
$sourceWidth = [int]$probe.streams[0].width
$sourceHeight = [int]$probe.streams[0].height

if ($sourceWidth -le 0 -or $sourceHeight -le 0) {
  throw "Could not determine source image dimensions."
}

if ($Width -eq 0 -and $Height -eq 0) {
  $Width = [int][Math]::Round($sourceWidth * $Scale)
  $Height = [int][Math]::Round($sourceHeight * $Scale)
} elseif ($Width -eq 0) {
  $Width = [int][Math]::Round($Height * $sourceWidth / $sourceHeight)
} elseif ($Height -eq 0) {
  $Height = [int][Math]::Round($Width * $sourceHeight / $sourceWidth)
}

if ($Width -le 0 -or $Height -le 0) {
  throw "Target dimensions must be greater than 0."
}

if (-not $OutputPath) {
  $OutputPath = Join-Path $inputItem.DirectoryName "$($inputItem.BaseName)_topaz_${Width}x${Height}.png"
}

$outputItem = New-Object System.IO.FileInfo($OutputPath)
$supportedOutput = @(".png", ".tif", ".tiff", ".jpg", ".jpeg", ".webp", ".bmp")
if ($supportedOutput -notcontains $outputItem.Extension.ToLowerInvariant()) {
  throw "Unsupported output image extension '$($outputItem.Extension)'. Supported: $($supportedOutput -join ', ')"
}

$env:TVAI_MODEL_DATA_DIR = $modelDir
$env:TVAI_MODEL_DIR = $modelDir

$topazFilter = "tvai_up=model=${Model}:h=${Height}:download=1:device=0:instances=0:estimate=0"

switch ($Fit) {
  "Crop" {
    $imageFilter = "${topazFilter},scale=w=${Width}:h=${Height}:flags=lanczos:force_original_aspect_ratio=increase,crop=${Width}:${Height}"
  }
  "Stretch" {
    $imageFilter = "${topazFilter},scale=${Width}:${Height}:flags=lanczos"
  }
  "Pad" {
    $imageFilter = "${topazFilter},scale=w=${Width}:h=${Height}:flags=lanczos:force_original_aspect_ratio=decrease,pad=${Width}:${Height}:-1:-1:color=black"
  }
}

$imageFilter = "${imageFilter},setsar=1"

$outputDir = Split-Path -Parent $OutputPath
if ($outputDir -and -not (Test-Path -LiteralPath $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Write-Host "Input:  $InputPath"
Write-Host "Output: $OutputPath"
Write-Host "Source: ${sourceWidth}x${sourceHeight}"
Write-Host "Target: ${Width}x${Height}, model ${Model}, fit ${Fit}"

$encodeArgs = @()
if (@(".jpg", ".jpeg") -contains $outputItem.Extension.ToLowerInvariant()) {
  $encodeArgs = @("-q:v", $JpegQuality)
}

& $ffmpeg `
  -hide_banner -y `
  -loop 1 `
  -framerate 25 `
  -t 0.24 `
  -i $InputPath `
  -vf $imageFilter `
  -frames:v 1 `
  -update 1 `
  @encodeArgs `
  $OutputPath

if ($LASTEXITCODE -ne 0) {
  throw "Topaz image upscale failed with exit code $LASTEXITCODE"
}

Write-Host "Done: $OutputPath"
