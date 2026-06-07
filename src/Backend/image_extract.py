import fitz
import os
import io
import base64
import zipfile
import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
VISION_MODEL = "llava-hf/llava-1.5-7b-hf"

MIN_WIDTH = 80
MIN_HEIGHT = 80

VISION_PROMPT = (
    "You are an expert technical data analyst. Your task is to describe this image "
    "comprehensively so it can be indexed in a vector database for semantic search. "
    "Follow these strict rules:\n"
    "1. Extract and explicitly write out all visible text, numbers, and labels.\n"
    "2. If it is a diagram or flowchart, describe the exact stages, relationships, and direction of flow/arrows.\n"
    "3. If it is a chart or graph, state the titles, axis labels, and key data points or trends.\n"
    "4. Start the description immediately with factual content. NEVER use preambles like "
    "'The image shows', 'Here is a diagram of', or 'This picture represents'.\n"
    "Provide a dense, highly detailed description in English, maximum 300 words."
)

def _to_jpeg_base64(img_bytes):
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"  [image_extract] Error with image conversion: {e}")
        return None

def pdf_extract(pdf_path):
    images = []

    try:
        pdf_file = fitz.open(pdf_path)
        for page_num in range(len(pdf_file)):
            page_content = pdf_file[page_num]
            for img_idx, img_info in enumerate(page_content.get_images(full=True)):
                xref = img_info[0]
                try:
                    pix = fitz.Pixmap(pdf_file, xref)

                    if pix.n - pix.alpha > 3:
                        pix = fitz.Pixmap(fitz.csRGB, pix)

                    if pix.width < MIN_WIDTH or pix.height < MIN_HEIGHT:
                        pix = None
                        continue

                    img_b64 = _to_jpeg_base64(pix.tobytes("jpeg"))
                    pix = None

                    if img_b64:
                        source = f"{pdf_path}_page{page_num + 1}_img{img_idx}"
                        images.append({
                            "base64": img_b64,
                            "page": page_num,
                            "source": source
                        })
                        print(f"  [image_extract] Found image: {source}")

                except Exception as e:
                    print(f"  [image_extract] Image error xref={xref} page{page_num + 1}: {e}")

        pdf_file.close()

    except Exception as e:
        print(f"[image_extract] Opening error {pdf_path}: {e}")

    return images

def _extract_images_docx(docx_path):
    images = []
    SUPPORTED = {"png", "jpg", "jpeg", "bmp", "gif", "tiff", "tif"}
    try:
        with zipfile.ZipFile(docx_path) as z:
            media_files = [
                f for f in z.namelist()
                if f.startswith("word/media/")
                and f.split(".")[-1].lower() in SUPPORTED
            ]
            for i, media_path in enumerate(media_files):
                try:
                    img_bytes = z.read(media_path)
                    img_b64 = _to_jpeg_base64(img_bytes)
                    if img_b64:
                        source = f"{docx_path}_img{i}"
                        images.append({
                            "base64": img_b64,
                            "page": 0,
                            "source": source
                        })
                        print(f"  [image_extract] Found image: {source}")
                except Exception as e:
                    print(f"  [image_extract] Image error {media_path}: {e}")
    except Exception as e:
        print(f"[image_extract] Opening error {docx_path}: {e}")
    return images

def _describe_image(img_b64, source):
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                    }
                },
                {
                    "type": "text",
                    "text": VISION_PROMPT
                }
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 400
    }
    try:
        r = requests.post(HF_API_URL, headers=headers,
                          json=payload, timeout=60)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"  [image_extract] Vision API error {r.status_code} "
                  f"for {source}: {r.text[:200]}")
            return ""
    except Exception as e:
        print(f"  [image_extract] Vision API exception for {source}: {e}")
        return ""

def extract_and_describe_images(file_path, last_modified, status):
    ext = file_path.split(".")[-1].lower()

    if ext == "pdf":
        images = pdf_extract(file_path)
    elif ext in ("docx", "doc"):
        images = _extract_images_docx(file_path)
    else:
        print(f"[image_extract] Unsupported file format: {file_path}")
        return []

    if not images:
        print(f"[image_extract] No images in {file_path}")
        return []

    print(f"[image_extract] Describing {len(images)} images from {file_path} "
          f"by Llama 3.2 Vision...")

    chunks = []
    for img in images:
        print(f"  [image_extract] Describing: {img['source']}")
        desc = _describe_image(img["base64"], img["source"])

        if not desc:
            print(f"  [image_extract] Empty description - skip {img['source']}")
            continue

        chunks.append({
            "content":       f"[IMAGE page {img['page'] + 1}]: {desc}",
            "source":        img["source"],
            "last_modified": last_modified,
            "tags":          ["image", "visual", ext],
            "status":        status,
            "type":          "image"
        })

    print(f"[image_extract] {file_path}: added {len(chunks)} image chunks")
    return chunks