# Topaz Video Upscale Recipe

Use this when Nate asks for another Topaz Video upscale job.

## What worked

- Topaz install: `C:\Program Files\Topaz Labs LLC\Topaz Video`
- Topaz FFmpeg: `C:\Program Files\Topaz Labs LLC\Topaz Video\ffmpeg.exe`
- Model directory: `C:\ProgramData\Topaz Labs LLC\Topaz Video\models`
- Required env vars before using `tvai_up` from normal PowerShell:
  - `TVAI_MODEL_DATA_DIR=C:\ProgramData\Topaz Labs LLC\Topaz Video\models`
  - `TVAI_MODEL_DIR=C:\ProgramData\Topaz Labs LLC\Topaz Video\models`
- Model used successfully: `prob-4`
- Encoder used successfully: `hevc_nvenc`
- Default target: `8100x1080`, `24 fps`, HEVC MP4.

Topaz CLI docs: https://docs.topazlabs.com/video-ai/advanced-functions-in-topaz-video-ai/command-line-interface

## Reuse command

From the repo root:

```powershell
.\tools\topaz-upscale.ps1 -InputPath "C:\path\to\video.mp4"
```

Useful options:

```powershell
.\tools\topaz-upscale.ps1 `
  -InputPath "C:\path\to\video.mp4" `
  -OutputPath "C:\path\to\video_topaz_8100x1080.mp4" `
  -Width 8100 `
  -Height 1080 `
  -Model prob-4 `
  -Fit Crop
```

`-Fit Crop` preserves aspect ratio and center-crops to exact dimensions. `-Fit Stretch` forces exact dimensions and may distort. `-Fit Pad` preserves aspect ratio with black padding.

## Last successful job

Input:

`C:\Users\nate-\Downloads\BackGround\grok-video-521445e4-96c8-4336-a8df-2f19f97f121b (1).mp4`

Output:

`C:\Users\nate-\Downloads\BackGround\grok-video-521445e4-96c8-4336-a8df-2f19f97f121b_topaz_8100x1080.mp4`

Verified output:

- `8100x1080`
- HEVC
- `24 fps`
- `241 frames`
- about `10.04s`
- about `21.4 MB`
