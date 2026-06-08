# Image Upscale Archive

Date: 2026-06-07

This archive records the image/video upscale helper work and the generated image outputs from this session.

## Scripts

- `tools/topaz-upscale.ps1`
  - Existing Topaz Video AI helper for video upscaling.
  - Uses bundled Topaz `ffmpeg.exe` and `tvai_up`.

- `tools/topaz-image-upscale.ps1`
  - Added still-image upscale helper.
  - Uses Topaz Video AI's bundled `ffmpeg.exe` / `ffprobe.exe`.
  - Feeds still images as a short loop for `tvai_up`, then exports one frame.
  - Adds `setsar=1` so outputs use square pixels.

## 21-9 Temple Image

Source:

- `C:\Users\nate-\Desktop\2Version.dancin\videos2\21-9.jpg`

Generated:

- `C:\Users\nate-\Desktop\2Version.dancin\videos2\21-9_topaz_8100x1080.png`
  - Final 8100x1080 blur-fill version.
  - Replaced the bad stretched Topaz version.

- `C:\Users\nate-\Desktop\2Version.dancin\videos2\21-9_8100x1080_blur_fill.png`
  - Same corrected 8100x1080 blur-fill variant kept separately.

- `C:\Users\nate-\Desktop\2Version.dancin\videos2\21-9_8100x1080_no_stretch.png`
  - No-stretch version with centered original proportions and blurred side fill.

- `C:\Users\nate-\Desktop\2Version.dancin\videos2\21-9_4200x1100_no_stretch.png`
  - Exact 4200x1100 version made from the no-stretch composition.
  - Verified 4200x1100, sample aspect ratio 1:1.

Notes:

- Direct 8100x1080 stretching made the character look distorted, so later versions preserve character proportions.
- `4200x1100` was made by aspect-preserving resize and padding to avoid character distortion.

## Bereginya Portrait

Source:

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya.png`

Topaz intermediate outputs:

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya_topaz_h1080.png`
  - Topaz upscale to 1080px tall.

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya_topaz_h1440.png`
  - Topaz upscale to 1440px tall.

Blur/edge-fill outputs:

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya_4200x1080.png`
  - 4200x1080 proportional portrait with local edge-fill background.

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya_2k_2560x1440.png`
  - 2560x1440 proportional portrait with local edge-fill background.

AI outpaint outputs:

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya_outpaint_base.png`
  - AI-generated wide extension of the original field/sky background.

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya_4200x1080_outpaint.png`
  - 4200x1080 output using the AI-extended field/sky background.
  - Better than the edge-fill version for natural left/right environment.

- `C:\Users\nate-\Desktop\DOM\dom app\bereginya_2k_2560x1440_outpaint.png`
  - 2560x1440 output using the AI-extended field/sky background.
  - Best-looking 2K version from this batch.

Notes:

- "2K" was treated as 2560x1440 (QHD).
- The AI outpaint was used because the requested background needed real left/right continuation, not stretched or blurred panels.

## Useful Commands

Make a still image exact-size with Topaz:

```powershell
.\tools\topaz-image-upscale.ps1 -InputPath "C:\path\image.png" -Width 4200 -Height 1100 -Fit Crop
```

Make a proportional height-based Topaz upscale:

```powershell
.\tools\topaz-image-upscale.ps1 -InputPath "C:\path\image.png" -Height 1440
```

Check output dimensions:

```powershell
& "C:\Program Files\Topaz Labs LLC\Topaz Video\ffprobe.exe" -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio,display_aspect_ratio -of default=noprint_wrappers=1 "C:\path\output.png"
```
