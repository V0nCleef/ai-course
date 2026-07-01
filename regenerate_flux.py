"""
Regenerate 4 images using Flux Schnell GGUF (much better quality than SD 1.5).
Flux Schnell: 4 steps, scheduler=beta, guidance=1.0, natural language prompts.
GGUF Q5_K_S fits in 10GB VRAM.
"""
import urllib.request, json, time, os, random, shutil

COMFY = "http://127.0.0.1:8188"
ASSETS = r"C:\AI presentations Output\ai-for-beginners\assets"
COMFY_OUTPUT = r"E:\ComfyUI\ComfyUI_windows_portable\ComfyUI\output"

# Flux Schnell GGUF Workflow — 4 steps only!
WORKFLOW = {
    "1": {
        "class_type": "UnetLoaderGGUF",
        "inputs": {"unet_name": "flux1-schnell-Q5_K_S.gguf"}
    },
    "2": {
        "class_type": "DualCLIPLoaderGGUF",
        "inputs": {
            "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
            "clip_name2": "clip_l.safetensors",
            "type": "flux"
        }
    },
    "3": {
        "class_type": "CLIPTextEncodeFlux",
        "inputs": {
            "clip": ["2", 0],
            "clip_l": "",
            "t5xxl": "",
            "guidance": 1.0
        }
    },
    "4": {
        "class_type": "VAELoader",
        "inputs": {"vae_name": "flux-vae-bf16.safetensors"}
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 1280, "height": 720, "batch_size": 1}
    },
    "6": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42,
            "steps": 4,
            "cfg": 1.0,
            "sampler_name": "euler",
            "scheduler": "beta",
            "denoise": 1.0,
            "model": ["1", 0],
            "positive": ["3", 0],
            "negative": ["3", 0],  # Flux: same conditioning for neg, cfg=1.0
            "latent_image": ["5", 0]
        }
    },
    "7": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["6", 0], "vae": ["4", 0]}
    },
    "8": {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": "flux_img", "images": ["7", 0]}
    }
}

# Flux Schnell works best with detailed natural language prompts.
# No "masterpiece" tags needed — it understands descriptive English.

IMAGES = [
    {
        "name": "what_is_ai",
        "prompt": "A warm educational illustration showing a friendly golden retriever dog sitting next to a calculator on a wooden desk. The dog looks happy and curious. The calculator displays simple math. Watercolor and colored pencil art style, soft warm lighting, clean composition, children's book illustration quality.",
        "desc": "Hond + trucje naast rekenmachine — warm, cartoon, educatief"
    },
    {
        "name": "ai_vs_software",
        "prompt": "A clean modern split-screen illustration. On the left side, an open cookbook with written recipe instructions and ingredient lists, representing traditional rule-based software. On the right side, a photo album filled with cute cat photographs, representing AI learning from examples. The two sides are separated by a subtle vertical line. Flat vector illustration style, warm navy blue and coral orange color palette, minimalist design, educational comparison visual.",
        "desc": "Kookboek vs. fotoalbum met kattenfoto's — modern, clean"
    },
    {
        "name": "how_ai_learns",
        "prompt": "A sunny outdoor scene in a park showing a child learning to ride a bicycle in three progressive stages connected by curved arrows. Stage one left: child with training wheels labeled Examples. Stage two center: child wobbling but finding balance labeled Patterns. Stage three right: child riding confidently with arms up labeled Improve. Green grass, blue sky with soft clouds, warm golden sunlight, educational infographic illustration style, clean design.",
        "desc": "3-stappen flow fietser — Voorbeelden→Patronen→Verbeteren"
    },
    {
        "name": "try_it",
        "prompt": "A modern silver laptop open on a warm wooden desk in a cozy home office. The laptop screen shows a friendly glowing AI chat interface with a welcoming smile icon and helpful text bubbles. Soft warm ambient lighting from a desk lamp on the left. A small green plant on the right side of the desk. Golden hour sunlight streaming through a window in the background. Professional yet inviting atmosphere, photorealistic style, shallow depth of field.",
        "desc": "Laptop met vriendelijke AI-assistent — uitnodigend, warm"
    },
]


def submit_prompt(prompt_text, filename_prefix, seed=None):
    """Submit to ComfyUI and return prompt_id."""
    if seed is None:
        seed = random.randint(0, 2**63 - 1)
    
    wf = json.loads(json.dumps(WORKFLOW))
    wf["3"]["inputs"]["clip_l"] = prompt_text
    wf["3"]["inputs"]["t5xxl"] = prompt_text
    wf["6"]["inputs"]["seed"] = seed
    wf["8"]["inputs"]["filename_prefix"] = filename_prefix
    
    payload = {"prompt": wf, "client_id": "hermes-flux"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{COMFY}/prompt", data=data,
                                  headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    
    if result.get("node_errors"):
        print(f"  ⚠ Node errors: {result['node_errors']}")
    
    return result["prompt_id"], seed


def wait_for_prompt(prompt_id, timeout=600):
    """Poll until complete. Flux Schnell is fast but needs model loading time (~30s first load)."""
    start = time.time()
    last_msg = 0
    while time.time() - start < timeout:
        time.sleep(3)
        elapsed = time.time() - start
        
        resp = urllib.request.urlopen(f"{COMFY}/history/{prompt_id}")
        h = json.loads(resp.read())
        
        if prompt_id in h:
            entry = h[prompt_id]
            status = entry.get('status', {})
            if status.get('status_str') == 'error':
                msgs = status.get('messages', ['unknown error'])
                print(f"  ❌ Error: {msgs[-1][:200]}")
                return None
            if 'outputs' in entry:
                images = []
                for node_id, outputs in entry['outputs'].items():
                    for img in outputs.get('images', []):
                        images.append(img)
                return images
        
        # Progress
        if elapsed > 10 and elapsed - last_msg > 15:
            qresp = urllib.request.urlopen(f"{COMFY}/queue")
            q = json.loads(qresp.read())
            running = len(q.get('queue_running', []))
            pending = len(q.get('queue_pending', []))
            print(f"  ⏳ {int(elapsed)}s (running={running}, pending={pending})")
            last_msg = elapsed
    
    print(f"  ❌ Timeout after {timeout}s")
    return None


def download_image(img_info, save_name):
    """Download from ComfyUI output to assets folder."""
    fn = img_info['filename']
    subfolder = img_info.get('subfolder', '')
    img_type = img_info.get('type', 'output')
    
    params = f"?filename={fn}&subfolder={subfolder}&type={img_type}"
    data = urllib.request.urlopen(f"{COMFY}/view{params}").read()
    
    outpath = os.path.join(ASSETS, save_name)
    with open(outpath, "wb") as f:
        f.write(data)
    return outpath


def main():
    os.makedirs(ASSETS, exist_ok=True)
    
    total = len(IMAGES)
    print("=" * 60)
    print(f"🎨 Flux Schnell GGUF — Regenerating {total} images")
    print(f"   Model: flux1-schnell-Q5_K_S.gguf (8.3GB)")
    print(f"   Resolution: 1280×720 (16:9)")
    print(f"   Settings: 4 steps, scheduler=beta, guidance=1.0")
    print(f"   Output: {ASSETS}")
    print("=" * 60)
    print()
    
    for i, img in enumerate(IMAGES):
        name = img["name"]
        fname = f"{name}.png"
        
        # Backup old version
        old_path = os.path.join(ASSETS, fname)
        if os.path.exists(old_path):
            backup = old_path.replace('.png', '_sd15_old.png')
            if not os.path.exists(backup):
                shutil.move(old_path, backup)
                print(f"   📦 Backed up old version → {name}_sd15_old.png")
        
        print(f"[{i+1}/{total}] 🎯 {fname}")
        print(f"   📝 {img['desc']}")
        print(f"   Prompt: {img['prompt'][:150]}...")
        
        # Submit
        try:
            prompt_id, seed = submit_prompt(img["prompt"], name)
            print(f"   📤 Submitted (id={prompt_id[:8]}..., seed={seed})")
        except Exception as e:
            print(f"   ❌ Submission failed: {e}")
            continue
        
        # Wait
        images = wait_for_prompt(prompt_id)
        if not images:
            print(f"   ❌ Generation failed for {fname}")
            continue
        
        # Download — note: GGUF ignores filename_prefix, files named be_*.png
        try:
            saved = download_image(images[0], fname)
            size_kb = os.path.getsize(saved) / 1024
            print(f"   ✅ Saved: {fname} ({size_kb:.0f} KB) — actual file: {images[0]['filename']}")
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
        
        print()
    
    print("=" * 60)
    print("🏁 Regeneration complete!")
    print("=" * 60)
    for f in sorted(os.listdir(ASSETS)):
        if f.endswith('.png') and not f.endswith('_sd15_old.png'):
            size_kb = os.path.getsize(os.path.join(ASSETS, f)) / 1024
            marker = "🆕" if any(f.startswith(x) for x in ["what_is_ai", "ai_vs_software", "how_ai_learns", "try_it"]) else "  "
            print(f"   {marker} {f} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
