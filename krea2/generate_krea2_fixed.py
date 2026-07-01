"""
Krea 2 Turbo — CORRECT settings from official template.
CFG 1.0, scheduler=simple, ConditioningZeroOut on SAME positive.
"""
import urllib.request, json, time, os, random

COMFY = "http://127.0.0.1:8188"
OUTDIR = r"C:\AI presentations Output\ai-for-beginners\krea2\assets"
os.makedirs(OUTDIR, exist_ok=True)

# Exact settings from the official Krea 2 template
WORKFLOW = {
    "10": {
        "class_type": "UNETLoader",
        "inputs": {
            "unet_name": "krea2_turbo_fp8_scaled.safetensors",
            "weight_dtype": "default"
        }
    },
    "11": {
        "class_type": "CLIPLoader",
        "inputs": {
            "clip_name": "qwen3vl_4b_fp8_scaled.safetensors",
            "type": "krea2",
            "device": "default"
        }
    },
    "12": {
        "class_type": "VAELoader",
        "inputs": {
            "vae_name": "qwen_image_vae.safetensors"
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "",
            "clip": ["11", 0]
        }
    },
    "13": {
        "class_type": "ConditioningZeroOut",
        "inputs": {
            "conditioning": ["6", 0]
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": 1280,
            "height": 720,
            "batch_size": 1
        }
    },
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42,
            "steps": 8,
            "cfg": 1.0,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "model": ["10", 0],
            "positive": ["6", 0],
            "negative": ["13", 0],
            "latent_image": ["5", 0]
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["12", 0]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "krea2",
            "images": ["8", 0]
        }
    }
}

IMAGES = [
    {"name": "hero_bg", "prompt": "Abstract artificial intelligence visualization with glowing neural network connections in deep navy blue tones accented by warm coral orange and golden light particles. Luminous interconnected nodes forming elegant brain-like patterns across a dark background. Soft atmospheric lighting, cinematic depth of field, professional technology art, warm and inviting atmosphere."},
    {"name": "what_is_ai", "prompt": "A warm educational illustration of a cute friendly golden retriever dog sitting next to a calculator on a clean wooden desk. The dog has a happy curious expression. The calculator displays simple math numbers. Soft watercolor and colored pencil art style, warm golden lighting, clean simple composition, professional childrens book illustration quality."},
    {"name": "ai_vs_software", "prompt": "A clean modern split-screen comparison illustration. Left panel shows an open cookbook with written recipe instructions representing traditional rule-based software. Right panel shows a photo album filled with cute cat photographs representing AI that learns from examples. A subtle vertical line separates the two sides. Flat vector illustration style, warm navy blue and coral orange colors, minimalist clean educational graphic."},
    {"name": "how_ai_learns", "prompt": "A sunny outdoor park scene showing a young child learning to ride a bicycle in three progressive stages moving from left to right. Left: child on bike with training wheels labeled Examples. Middle: child wobbling but finding balance labeled Patterns. Right: child riding confidently with arms raised in celebration labeled Improve. Curved arrows connecting the stages. Blue sky with soft clouds, green grass, warm golden sunlight. Clean educational infographic illustration."},
    {"name": "gen_ai_showcase", "prompt": "An elegant art gallery wall displaying three framed artworks in a triptych arrangement side by side. Left frame: a beautiful mountain landscape at golden sunset. Center frame: an artistic painted portrait of a woman with soft features. Right frame: colorful abstract geometric shapes in coral orange and gold tones. Warm museum gallery lighting, dark navy wall backdrop, professional art exhibition quality."},
    {"name": "ai_types", "prompt": "A clean three column infographic layout with large simple icons on a warm professional background. Left column: a stylized cloud icon labeled Cloud AI with soft blue glow. Middle column: a computer monitor icon labeled Local AI with warm coral glow. Right column: a steering wheel harness icon labeled AI Harness with golden glow. Modern corporate flat design style, simple clear icons, warm navy and coral color scheme."},
    {"name": "ai_everywhere", "prompt": "A glowing planet earth globe floating in space, surrounded by orbiting colorful icons representing different industries: a film movie camera, music notes, a medical cross for healthcare, a car for transportation, and an artist paint palette for art. All connected by luminous golden network lines circling the globe. Warm cosmic navy blue background with soft stars. Hopeful optimistic atmosphere, professional infographic quality."},
    {"name": "try_it", "prompt": "A modern silver laptop open on a warm wooden desk in a cozy home office setting. The laptop screen displays a friendly glowing AI assistant chat interface with a warm welcoming smile icon and helpful text bubbles. Soft warm ambient lighting from a desk lamp on the left side. A small green potted plant on the right. Golden hour sunlight streaming through a background window. Professional yet inviting atmosphere, photorealistic style, clean straight laptop edges, shallow depth of field."},
    {"name": "making_of", "prompt": "A four step horizontal creative process flow from left to right on a warm professional background. First: a glowing golden lightbulb icon representing Idea. Second: an artist paint palette with colorful brushes representing Creativity. Third: a computer screen with code lines representing Programming. Fourth: a presentation screen with charts representing Final Output. Connected by flowing curved golden arrows. Modern flat design illustration, clean professional composition."},
]

# Delete old test images
for f in os.listdir(OUTDIR):
    if f.startswith("test_") or f.startswith("krea2_t"):
        os.remove(os.path.join(OUTDIR, f))

print("=" * 60)
print("🎨 Krea 2 Turbo — CORRECT SETTINGS")
print("   CFG 1.0 | scheduler=simple | 8 steps | 1280×720")
print("   ConditioningZeroOut on same positive (template-correct)")
print("=" * 60)

for i, img in enumerate(IMAGES):
    name = img["name"]
    fname = f"{name}.png"
    outpath = os.path.join(OUTDIR, fname)
    
    if os.path.exists(outpath):
        sz = os.path.getsize(outpath) / 1024
        print(f"\n[{i+1}/9] ⏭ {fname} ({sz:.0f} KB) — exists, skipping")
        continue
    
    print(f"\n[{i+1}/9] 🎯 {fname}")
    print(f"   {img['prompt'][:100]}...")
    
    seed = random.randint(0, 2**63 - 1)
    wf = json.loads(json.dumps(WORKFLOW))
    wf["6"]["inputs"]["text"] = img["prompt"]
    wf["3"]["inputs"]["seed"] = seed
    wf["9"]["inputs"]["filename_prefix"] = name
    
    payload = {"prompt": wf, "client_id": "krea2-fixed"}
    data = json.dumps(payload).encode('utf-8')
    
    try:
        req = urllib.request.Request(f"{COMFY}/prompt", data=data,
                                      headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        
        if result.get("node_errors"):
            print(f"   ❌ Node errors: {result['node_errors']}")
            continue
        
        pid = result["prompt_id"]
        print(f"   📤 Submitted (seed={seed})")
    except Exception as e:
        print(f"   ❌ Submit: {e}")
        continue
    
    start = time.time()
    while time.time() - start < 300:
        time.sleep(3)
        try:
            hresp = urllib.request.urlopen(f"{COMFY}/history/{pid}")
            h = json.loads(hresp.read())
        except:
            continue
        
        if pid in h:
            entry = h[pid]
            s = entry.get('status', {}).get('status_str', '?')
            
            if s == 'error':
                msgs = entry['status'].get('messages', ['?'])
                print(f"   ❌ {str(msgs[-1])[:250]}")
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
        if elapsed >= 15 and elapsed % 20 <= 3:
            print(f"   ⏳ {elapsed}s...")
    else:
        print(f"   ❌ Timeout")

print("\n🏁 Done! Krea 2 assets:")
for f in sorted(os.listdir(OUTDIR)):
    if f.endswith('.png'):
        sz = os.path.getsize(os.path.join(OUTDIR, f)) / 1024
        print(f"   📁 {f} ({sz:.0f} KB)")
