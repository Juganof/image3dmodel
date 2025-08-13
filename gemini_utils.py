import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# Reads either name; set one of these in Replit Secrets.
def _client():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY in Secrets.")
    return genai.Client(api_key=key)

# ---- Text idea (Gemini) ----
def generate_makerworld_idea() -> str:
    client = _client()
    prompt = open("prompts/makerworld_idea_prompt.txt", "r", encoding="utf-8").read()
    resp = client.models.generate_content(
        model="gemini-2.0-flash",          # safe, widely available
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        # keep config minimal for compatibility with older SDKs
        config=types.GenerateContentConfig(
            temperature=0.6,
        ),
    )
    return (resp.text or "").strip()

# ---- Image (Imagen 4) ----
def generate_image_with_imagen(prompt: str, out_path: str, n_images: int = 1, aspect_ratio: str = "1:1"):
    client = _client()
    resp = client.models.generate_images(
        model="imagen-4.0-generate-preview-06-06",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=n_images,
            aspect_ratio=aspect_ratio,
        ),
    )
    if not resp.generated_images:
        raise RuntimeError("No images returned from Imagen 4.")
    img = resp.generated_images[0].image
    data = getattr(img, "image_bytes", None) or getattr(img, "imageBytes", None) or img
    Image.open(BytesIO(data)).save(out_path)
    return out_path
