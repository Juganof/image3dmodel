import argparse
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from gemini_utils import generate_makerworld_idea, generate_image_with_imagen
from hitem3d_client import process_image_with_hitem3d

def main():
    parser = argparse.ArgumentParser(description="Idea → Imagen 4 → Hitem3D pipeline")
    parser.add_argument("--out", default="output", help="Output folder (default: output)")
    parser.add_argument("--idea", default=None, help="Provide your own idea text (skips Gemini idea generation)")
    parser.add_argument("--image-prompt", default=None, help="Provide your own image prompt (skips prompt crafting)")
    parser.add_argument("--formats", default=os.getenv("HITEM3D_DOWNLOAD_FORMATS","glb,obj,stl"), help="Comma-separated formats to try (glb,obj,stl)")
    parser.add_argument("--timeout", type=int, default=int(os.getenv("HITEM3D_WAIT_MINUTES","20")), help="Max wait minutes on Hitem3D (default from env or 20)")
    parser.add_argument("--headful", action="store_true", help="Run browser non-headless for debugging")
    args = parser.parse_args()

    load_dotenv()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(out_dir / "run.log", mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    # 1) Generate a MakerWorld-ready idea (if not provided)
    if args.idea:
        idea_text = args.idea.strip()
    else:
        idea_text = generate_makerworld_idea()

    idea_path = out_dir / "idea.txt"
    idea_path.write_text(idea_text, encoding="utf-8")
    logger.info("[ok] Saved idea → %s", idea_path)

    # 2) Craft an image prompt if not provided
    if args.image_prompt:
        prompt = args.image_prompt.strip()
    else:
        prompt = (
            "Clean orthographic/isometric studio render of the product described: "
            f"{idea_text.splitlines()[0]} — minimalistic, neutral white background, "
            "front or 3/4 view, sharp edges, even lighting, "
            "no text, no branding, centered, high detail."
        )

    # 2) Generate image with Imagen 4
    img_path = out_dir / "imagen.png"
    generate_image_with_imagen(prompt, img_path)
    logger.info("[ok] Saved generated image → %s", img_path)

    # 3) Upload to Hitem3D and download result(s)
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    downloaded = process_image_with_hitem3d(
        image_path=str(img_path),
        out_dir=str(out_dir),
        prefer_formats=formats,
        wait_minutes=args.timeout,
        headless=not args.headful
    )

    if downloaded:
        logger.info("[ok] Downloaded: %s", ", ".join(downloaded))
    else:
        logger.warning(
            "[warn] No model files were downloaded. Try --headful to debug, increase --timeout, or check site requirements."
        )

if __name__ == "__main__":
    main()
