import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

DEFAULT_IDEA_SYSTEM = open("prompts/makerworld_idea_prompt.txt","r",encoding="utf-8").read()

def _client():
    # The client picks up GEMINI_API_KEY from the environment.
    return genai.Client()

def generate_makerworld_idea() -> str:
    client = _client()
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role":"user","parts":[{"text": DEFAULT_IDEA_SYSTEM}]}],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        ),
    )
    return (resp.text or "").strip()

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
