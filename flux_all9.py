"""
All 9 images with Flux Schnell GGUF — proven quality.
4 steps, cfg=1.0, euler/beta, 1280×720.
"""
import urllib.request, json, time, os, random, shutil

COMFY = "http://127.0.0.1:8188"
ASSETS = r"C:\AI presentations Output\ai-for-beginners\assets"
os.makedirs(ASSETS, exist_ok=True)

WORKFLOW = {
    "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-schnell-Q5_K_S.gguf"}},
    "2": {"class_type": "DualCLIPLoaderGGUF", "inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}},
    "3": {"class_type": "CLIPTextEncodeFlux", "inputs": {"clip": ["2", 0], "clip_l": "", "t5xxl": "", "guidance": 1.0}},
    "4": {"class_type": "VAELoader", "inputs": {"vae_name": "flux-vae-bf16.safetensors"}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1280, "height": 720, "batch_size": 1}},
    "6": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "beta", "denoise": 1.0, "model": ["1", 0], "positive": ["3", 0], "negative": ["3", 0], "latent_image": ["5", 0]}},
    "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["4", 0]}},
    "8": {"class_type": "SaveImage", "inputs": {"filename_prefix": "flux", "images": ["7", 0]}}
}

IMAGES = [
    ("hero_bg", "Abstract artificial intelligence visualization with glowing neural network connections in deep navy blue tones accented by warm coral orange and golden light particles. Luminous interconnected nodes forming elegant brain-like patterns. Soft atmospheric lighting, cinematic depth of field, professional technology background, warm and inviting atmosphere."),
    ("what_is_ai", "A warm educational illustration of a cute friendly golden retriever dog sitting next to a calculator on a clean wooden desk. The dog has a happy curious expression, the calculator shows simple numbers. Soft watercolor and colored pencil art style, warm golden lighting, clean simple composition, childrens book illustration quality."),
    ("ai_vs_software", "A clean modern split-screen comparison illustration. Left side: an open cookbook with written recipe instructions representing traditional rule-based software. Right side: a photo album filled with cute cat photographs representing AI that learns from examples. A subtle vertical line separates them. Flat vector illustration style, warm navy blue and coral orange colors, minimalist educational graphic."),
    ("how_ai_learns", "A sunny outdoor park scene showing a child learning to ride a bicycle in three progressive stages from left to right. First stage: child on bike with training wheels labeled Examples. Second: child wobbling but finding balance labeled Patterns. Third: child riding confidently with arms raised labeled Improve. Curved arrows connecting stages. Blue sky, green grass, warm golden sunlight. Educational infographic illustration."),
    ("gen_ai_showcase", "An elegant art gallery wall displaying three framed artworks in a triptych. Left frame: beautiful mountain landscape at golden sunset. Center frame: artistic painted portrait of a woman. Right frame: colorful abstract geometric shapes in coral and gold. Warm museum gallery lighting, dark navy wall, professional quality."),
    ("ai_types", "A clean three column infographic with large simple icons on warm background. Left: stylized cloud icon for Cloud AI. Middle: computer monitor icon for Local AI. Right: steering wheel harness icon for AI Harness. Modern corporate flat design, warm navy and coral color scheme, simple clear icons."),
    ("ai_everywhere", "A glowing planet earth globe floating in space, surrounded by orbiting icons: film camera, music notes, medical cross, car, artist palette. All connected by luminous golden network lines. Warm cosmic navy blue background with soft stars. Hopeful optimistic atmosphere, professional infographic quality."),
    ("try_it", "A modern silver laptop open on a warm wooden desk in a cozy home office. The laptop screen shows a friendly AI assistant chat interface with a warm welcoming smile. Soft desk lamp lighting on left, small green plant on right, golden hour sunlight through window. Professional inviting atmosphere, photorealistic, clean straight laptop."),
    ("making_of", "A four step horizontal creative process flow from left to right. First: glowing golden lightbulb for Idea. Second: artist paint palette for Creativity. Third: computer screen with code for Programming. Fourth: presentation screen with charts for Output. Connected by flowing golden arrows. Modern flat design, clean professional."),
]

print("=" * 60)
print("🎨 Flux Schnell GGUF — all 9 images at 1280×720")
print("   4 steps | CFG 1.0 | euler/beta")
print("=" * 60)

for i, (name, prompt) in enumerate(IMAGES):
    fname = f"{name}.png"
    outpath = os.path.join(ASSETS, fname)
    
    if os.path.exists(outpath) and os.path.getsize(outpath) > 800000:
        sz = os.path.getsize(outpath) / 1024
        print(f"\n[{i+1}/9] ⏭ {fname} ({sz:.0f} KB) — exists")
        continue
    
    print(f"\n[{i+1}/9] 🎯 {fname}")
    
    seed = random.randint(0, 2**63 - 1)
    wf = json.loads(json.dumps(WORKFLOW))
    wf["3"]["inputs"]["clip_l"] = prompt
    wf["3"]["inputs"]["t5xxl"] = prompt
    wf["6"]["inputs"]["seed"] = seed
    wf["8"]["inputs"]["filename_prefix"] = name
    
    payload = {"prompt": wf, "client_id": "flux-batch"}
    data = json.dumps(payload).encode('utf-8')
    
    try:
        req = urllib.request.Request(f"{COMFY}/prompt", data=data,
                                      headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        if result.get("node_errors"):
            print(f"   ❌ {result['node_errors']}")
            continue
        pid = result["prompt_id"]
        print(f"   📤 seed={seed}")
    except Exception as e:
        print(f"   ❌ {e}")
        continue
    
    start = time.time()
    while time.time() - start < 360:
        time.sleep(5)
        try:
            hresp = urllib.request.urlopen(f"{COMFY}/history/{pid}")
            h = json.loads(hresp.read())
        except:
            continue
        
        if pid in h:
            entry = h[pid]
            s = entry.get('status', {}).get('status_str', '?')
            if s == 'error':
                print(f"   ❌ {str(entry['status'].get('messages',['?'])[-1])[:200]}")
                break
            if 'outputs' in entry:
                for nid, outs in entry['outputs'].items():
                    for oimg in outs.get('images', []):
                        fn = oimg['filename']
                        params = f"?filename={fn}&subfolder={oimg.get('subfolder','')}&type={oimg.get('type','output')}"
                        imgdata = urllib.request.urlopen(f"{COMFY}/view{params}").read()
                        with open(outpath, "wb") as f:
                            f.write(imgdata)
                        print(f"   ✅ {len(imgdata)/1024:.0f} KB in {int(time.time()-start)}s")
                break
        
        elapsed = int(time.time() - start)
        if elapsed >= 20 and elapsed % 20 <= 5:
            print(f"   ⏳ {elapsed}s...")
    else:
        print(f"   ❌ Timeout")

print("\n🏁 Done!")
for f in sorted(os.listdir(ASSETS)):
    if f.endswith('.png'):
        sz = os.path.getsize(os.path.join(ASSETS, f)) / 1024
        print(f"   📁 {f} ({sz:.0f} KB)")
