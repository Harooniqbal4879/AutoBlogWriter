import os
import requests
from PIL import Image
from io import BytesIO

def download_image(url: str, save_dir: str, filename: str = None) -> str:
    """Download image from URL and save locally. Returns saved file path."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if not filename:
        filename = os.path.basename(url.split('?')[0])
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            filename += '.png'
    save_path = os.path.join(save_dir, filename)
    response = requests.get(url)
    response.raise_for_status()
    with open(save_path, 'wb') as f:
        f.write(response.content)
    return save_path

def process_image(image_path: str, output_dir: str, resize: tuple = (1024, 1024), fmt: str = 'PNG') -> str:
    """Resize and convert image format. Returns processed file path."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = img.resize(resize)
    base = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(output_dir, f"{base}_processed.{fmt.lower()}")
    img.save(out_path, fmt)
    return out_path

def pipeline(image_urls: list, save_dir: str, output_dir: str, resize: tuple = (1024, 1024), fmt: str = 'PNG') -> list:
    """Download, process, and store images from URLs. Returns list of processed file paths."""
    processed_files = []
    for url in image_urls:
        try:
            raw_path = download_image(url, save_dir)
            proc_path = process_image(raw_path, output_dir, resize, fmt)
            processed_files.append(proc_path)
        except Exception as e:
            print(f"Error processing {url}: {e}")
    return processed_files
