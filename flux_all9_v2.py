"""
Regenerate all 9 images with Flux Schnell GGUF.
NO text in images — text will be added as slide overlays.
Dutch text requirement met via HTML/CSS overlays in slides.
"""
import urllib.request, json, time, os, random

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

# NO TEXT references in prompts — Flux can't render readable text.
# Dutch labels will be HTML/CSS overlays in the slides.
IMAGES = [
    ("hero_bg", "Abstract artificial intelligence visualization, glowing neural network connections in deep navy blue with warm coral orange and golden light particles, luminous interconnected nodes forming elegant brain-like patterns, soft atmospheric lighting, cinematic depth of field, professional technology background art, warm and inviting atmosphere, no text no labels no words"),
    ("what_is_ai", "A warm educational illustration of a cute friendly golden retriever dog sitting next to a modern calculator on a clean wooden desk, the dog has a happy curious expression looking at the viewer, soft watercolor and colored pencil art style, warm golden sunlight through a window, clean simple composition, professional childrens book illustration, no text no words no labels"),
    ("ai_vs_software", "Clean modern split-screen comparison, left half showing an open cookbook with recipe pages on a kitchen table representing traditional rules, right half showing a photo album filled with cute cat photographs on a coffee table representing learning from examples, subtle division between the two sides, flat vector illustration style, warm navy blue and coral orange colors, minimalist educational graphic, no text no words"),
    ("how_ai_learns", "Sunny outdoor park scene, a young child learning to ride a bicycle in three progressive stages from left to right connected by curved arrows, first stage child with training wheels on a bike, second stage child wobbling and finding balance, third stage child riding confidently with arms raised in celebration, blue sky with soft white clouds, green grass, warm golden sunlight, clean educational illustration, no text no words no labels"),
    ("gen_ai_showcase", "Elegant art gallery wall displaying three framed artworks in a horizontal triptych arrangement, left frame contains a beautiful mountain landscape at golden sunset, center frame contains an artistic painted portrait of a woman, right frame contains colorful abstract geometric shapes in coral orange and gold tones, warm museum gallery lighting, dark navy wall backdrop, professional art exhibition quality, no text"),
    ("ai_types", "Clean three column layout with large simple icons on a warm professional background, left column features a stylized cloud symbol representing online services, middle column features a desktop computer monitor symbol representing local computing, right column features a steering wheel symbol representing control systems, modern corporate flat design style, warm navy blue and coral orange color scheme, simple clear icons, no text no words"),
    ("ai_everywhere", "Glowing planet earth globe floating in outer space, surrounded by orbiting colorful symbols representing different industries, a film movie camera, musical notes, a red medical cross, an automobile, and an artist paint palette, all connected by luminous golden network lines circling the globe, warm cosmic navy blue background with soft stars, hopeful optimistic atmosphere, professional infographic style, no text"),
    ("try_it", "A modern silver laptop open on a warm wooden desk in a cozy home office, the laptop screen displays a friendly glowing AI chat interface with a warm welcoming smile icon and helpful looking chat bubbles, soft warm ambient lighting from a stylish desk lamp on the left side, a small green potted plant on the right side of the desk, golden hour sunlight streaming through a window in the background, professional yet inviting atmosphere, photorealistic, no text on screen"),
    ("making_of", "Four step horizontal creative process flow on a warm professional background, first step shows a glowing golden lightbulb representing ideas, second step shows an artist paint palette with colorful brushes representing creativity, third step shows a computer monitor with colorful code lines representing programming, fourth step shows a presentation screen with colorful charts representing final output, all connected by flowing curved golden arrows, modern flat design illustration, clean professional composition, no text"),
]

print("=" * 60)
print("🎨 Flux Schnell GGUF — Regenerating ALL 9 images")
print("   1280×720 | 4 steps | CFG 1.0 | euler/beta")
print("   NO text in images — Dutch labels via slide overlays")
print("=" * 60)

for i, (name, prompt) in enumerate(IMAGES):
    fname = f"{name}.png"
    outpath = os.path.join(ASSETS, fname)
    
    print(f"\n[{i+1}/9] {fname}")
    print(f"   {prompt[:100]}...")
    
    if os.path.exists(outpath):
        os.remove(outpath)
    
    seed = random.randint(0, 2**63 - 1)
    wf = json.loads(json.dumps(WORKFLOW))
    wf["3"]["inputs"]["clip_l"] = prompt
    wf["3"]["inputs"]["t5xxl"] = prompt
    wf["6"]["inputs"]["seed"] = seed
    wf["8"]["inputs"]["filename_prefix"] = name
    
    payload = {"prompt": wf, "client_id": "flux-v2"}
    data = json.dumps(payload).encode('utf-8')
    
    try:
        req = urllib.request.Request(f"{COMFY}/prompt", data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        if result.get("node_errors"):
            print(f"   ❌ {result['node_errors']}")
            continue
        pid = result["prompt_id"]
    except Exception as e:
        print(f"   ❌ {e}")
        continue
    
    start = time.time()
    while time.time() - start < 300:
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

print("\n" + "=" * 60)
print("🏁 All 9 regenerated!")
for f in sorted(os.listdir(ASSETS)):
    if f.endswith('.png'):
        sz = os.path.getsize(os.path.join(ASSETS, f)) / 1024
        print(f"   📁 {f} ({sz:.0f} KB)")
