"""
Batch generation of 9 AI images for the Dutch AI beginners course.
Uses SD 1.5 via ComfyUI REST API. 1280x720, 16:9.
"""
import urllib.request, json, time, os, shutil

COMFY = "http://127.0.0.1:8188"
ASSETS = r"C:\AI presentations Output\ai-for-beginners\assets"
COMFY_OUTPUT = r"E:\ComfyUI\ComfyUI_windows_portable\ComfyUI\output"

# Cleaned SD 1.5 workflow (no _comment/_meta keys — they cause 500 errors)
WORKFLOW = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42, "steps": 25, "cfg": 7.0,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
            "model": ["4", 0], "positive": ["6", 0],
            "negative": ["7", 0], "latent_image": ["5", 0]
        }
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "v1-5-pruned-emaonly-fp16.safetensors"}
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 1280, "height": 720, "batch_size": 1}
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "", "clip": ["4", 1]}
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "", "clip": ["4", 1]}
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": "img", "images": ["8", 0]}
    }
}

NEGATIVE = "text, watermark, signature, letters, words, logo, people, faces, distorted faces, ugly, blurry, low quality, bad anatomy, extra limbs, disfigured, harsh lighting, cold blue sterile, oversaturated"

IMAGES = [
    {
        "name": "hero_bg",
        "prompt": "abstract artificial intelligence visualization, glowing neural network connections in deep navy blue with warm coral orange and golden accents, luminous interconnected nodes forming brain-like patterns, soft atmospheric lighting, professional elegant technology background, bokeh light particles, cinematic depth of field, warm inviting atmosphere, masterpiece, high quality"
    },
    {
        "name": "what_is_ai",
        "prompt": "cute friendly golden retriever dog performing a playful trick next to a calculator on a desk, warm watercolor cartoon illustration style, educational children's book art, soft warm colors golden and coral, simple clear composition, inviting and playful atmosphere, clean white background with soft shadows, high quality illustration"
    },
    {
        "name": "ai_vs_software",
        "prompt": "split comparison composition, left side showing a traditional cookbook with recipe pages open, right side showing a modern photo album filled with cute cat photos, modern clean vector illustration style, warm soft lighting, educational visual comparison, soft pastel navy blue and coral colors, minimalist flat design, high quality"
    },
    {
        "name": "how_ai_learns",
        "prompt": "three step learning process illustration, a person learning to ride a bicycle in three progressive stages: first step with training wheels labeled examples, second step finding balance labeled patterns, third step riding confidently labeled improve, warm sunny outdoor park scene with trees, educational infographic style on a path, clear flow arrows connecting stages, soft natural golden lighting, high quality illustration"
    },
    {
        "name": "gen_ai_showcase",
        "prompt": "art gallery wall with three framed artworks displayed side by side in a triptych arrangement: left frame shows a beautiful mountain landscape at golden sunset, center frame shows an artistic painted portrait of a woman, right frame shows colorful abstract geometric shapes in coral and gold, warm museum gallery lighting, elegant dark navy wall, professional art exhibition, high quality"
    },
    {
        "name": "ai_types",
        "prompt": "three column clean infographic layout with large simple icons on warm background: left column shows a stylized cloud icon labeled Cloud AI with soft blue glow, middle column shows a computer monitor icon labeled Local AI with warm coral glow, right column shows a steering wheel harness icon labeled AI Harness with golden glow, modern corporate style, simple clear icons, warm professional navy and coral color scheme, minimalist flat design"
    },
    {
        "name": "ai_everywhere",
        "prompt": "glowing planet earth globe centered, surrounded by orbiting iconic symbols representing different industries: film movie camera, music notes, medical cross healthcare, car transportation, paint palette art, all connected by luminous golden network lines circling the globe, warm cosmic navy blue background with soft stars, professional infographic style, hopeful optimistic atmosphere, high quality"
    },
    {
        "name": "try_it",
        "prompt": "modern silver laptop open on a warm wooden desk, laptop screen displaying a friendly glowing AI assistant interface with a warm welcoming smile, soft warm ambient lighting from a desk lamp, cozy home office setting with a small plant, warm golden hour sunlight through window, inviting comfortable atmosphere, professional yet approachable, high quality photograph style"
    },
    {
        "name": "making_of",
        "prompt": "four step horizontal creative process flow from left to right on warm background: first a glowing golden lightbulb icon representing idea, second an artist paint palette with brushes representing creativity, third a computer screen with colorful code representing programming, fourth a presentation screen with charts representing final output, all connected by flowing curved golden arrows, warm creative studio atmosphere, modern flat design illustration, professional clean composition, high quality"
    },
]


def submit_prompt(prompt_text, negative_text, filename_prefix, seed=None):
    """Submit a prompt to ComfyUI and return prompt_id."""
    import random
    if seed is None:
        seed = random.randint(0, 2**63 - 1)
    
    wf = json.loads(json.dumps(WORKFLOW))  # deep copy
    wf["3"]["inputs"]["seed"] = seed
    wf["6"]["inputs"]["text"] = prompt_text
    wf["7"]["inputs"]["text"] = negative_text
    wf["9"]["inputs"]["filename_prefix"] = filename_prefix
    
    payload = {"prompt": wf, "client_id": "hermes-batch"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{COMFY}/prompt", data=data,
                                  headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    
    if result.get("node_errors"):
        print(f"  ⚠ Node errors: {result['node_errors']}")
    
    return result["prompt_id"], seed


def wait_for_prompt(prompt_id, timeout=300):
    """Poll until prompt completes, return output images."""
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        resp = urllib.request.urlopen(f"{COMFY}/history/{prompt_id}")
        h = json.loads(resp.read())
        if prompt_id in h:
            entry = h[prompt_id]
            status = entry.get('status', {})
            if status.get('status_str') == 'error':
                print(f"  ❌ Error: {status.get('messages', 'unknown')}")
                return None
            if 'outputs' in entry:
                images = []
                for node_id, outputs in entry['outputs'].items():
                    for img in outputs.get('images', []):
                        images.append(img)
                return images
        # Progress check
        elapsed = time.time() - start
        if elapsed > 10 and int(elapsed) % 15 == 0:
            qresp = urllib.request.urlopen(f"{COMFY}/queue")
            q = json.loads(qresp.read())
            print(f"  ⏳ {int(elapsed)}s (running={len(q.get('queue_running',[]))}, pending={len(q.get('queue_pending',[]))})")
    
    print(f"  ❌ Timeout after {timeout}s")
    return None


def download_image(img_info, save_name):
    """Download an image from ComfyUI output to assets folder."""
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
    print(f"🎨 Generating {total} images at 1280×720 (SD 1.5, 25 steps, CFG 7.0)")
    print(f"   Output: {ASSETS}\n")
    
    for i, img in enumerate(IMAGES):
        name = img["name"]
        fname = f"{name}.png"
        outpath = os.path.join(ASSETS, fname)
        
        # Skip if already exists
        if os.path.exists(outpath):
            print(f"[{i+1}/{total}] ⏭ {fname} — already exists, skipping")
            continue
        
        print(f"[{i+1}/{total}] 🎯 {fname}")
        print(f"   Prompt: {img['prompt'][:120]}...")
        
        # Submit
        try:
            prompt_id, seed = submit_prompt(img["prompt"], NEGATIVE, name)
            print(f"   Submitted (id={prompt_id[:8]}..., seed={seed})")
        except Exception as e:
            print(f"   ❌ Submission failed: {e}")
            continue
        
        # Wait
        images = wait_for_prompt(prompt_id)
        if not images:
            print(f"   ❌ Generation failed for {fname}")
            continue
        
        # Download
        try:
            saved = download_image(images[0], fname)
            size_kb = os.path.getsize(saved) / 1024
            print(f"   ✅ Saved: {fname} ({size_kb:.0f} KB)")
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
        
        print()
    
    print("🏁 All done! Check assets folder.")
    # List all generated files
    for f in sorted(os.listdir(ASSETS)):
        if f.endswith('.png'):
            size_kb = os.path.getsize(os.path.join(ASSETS, f)) / 1024
            print(f"   📁 {f} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
