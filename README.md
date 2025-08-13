# Image→3D Pipeline (Gemini + Imagen 4 + Hitem3D)

This small Python app does three things:

1) Uses the **Gemini API** to generate an idea for a 3D-printable model (suitable for MakerWorld).  
2) Uses **Imagen 4** (via the Gemini API) to generate a reference image from a text prompt.  
3) **Uploads** that image to **hitem3d.ai**, waits for processing, and **downloads** the resulting 3D model (GLB/OBJ/STL) into an `output/` folder.

> ⚠️ **Important notes**
>
> * You need a **GEMINI_API_KEY** from Google AI Studio.
> * Hitem3D has no public API docs at this time; this project automation uses **Playwright** to drive the web UI. Be sure your usage complies with their Terms, and be prepared to adjust selectors if the UI changes.
>
> * You must provide your own prompts/keys and ensure generated content complies with all platform policies.

---

## Quick start

### 1) Requirements

- Python 3.10+
- `pip install -r requirements.txt`
- Install Playwright browsers: `python -m playwright install chromium`

### 2) Environment

Copy `.env.example` → `.env` and set:

```
GEMINI_API_KEY=YOUR_KEY_HERE
# optional
HITEM3D_HEADLESS=true
HITEM3D_WAIT_MINUTES=20
HITEM3D_DOWNLOAD_FORMATS=glb,obj,stl
```

### 3) Run

- Full pipeline (idea → image → 3D):
```
python app.py --out output/
```

- Provide your own image prompt (skip idea generation):
```
python app.py --image-prompt "isometric studio render of a low-poly desk organizer, neutral lighting, white background"
```

- Provide both idea text and image prompt:
```
python app.py --idea "Parametric honeycomb pen holder ..." --image-prompt "orthographic studio render of a honeycomb pen holder ..."
```

- Control formats and timeout:
```
python app.py --formats stl,obj --timeout 30
```

Outputs land in `output/`:
- `idea.txt` – MakerWorld-ready idea
- `imagen.png` – generated reference image
- `model.*` – one or more of GLB/OBJ/STL, depending on availability
- `run.log` – log file for the latest run (overwritten each time)

---

## How it works

- `gemini_utils.py`
  - `generate_makerworld_idea(...)` uses **Gemini 2.5 Flash** to produce a concise, printable-friendly idea with short specs.
  - `generate_image_with_imagen(...)` calls **Imagen 4** (`imagen-4.0-generate-preview-06-06`) to create an image.
- `hitem3d_client.py`
  - Automates https://hitem3d.ai/ with Playwright: uploads the image, waits for generation, then captures download links and saves files.
  - Selectors are resilient but you may need to tweak them if the site updates its UI.

---

## Troubleshooting

- **Playwright timeouts**: Increase `--timeout` or set `HITEM3D_WAIT_MINUTES`.
- **No download links found**: UI may have changed or login/credits may be required. Run with `--headful` to see what's happening.
- **Gemini key issues**: Verify `GEMINI_API_KEY` is exported in your shell or `.env` and that your account has access to Imagen 4 preview.

---

## License

MIT
