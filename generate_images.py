#!/usr/bin/env python3
"""Batch generate 9 AI images for the AI beginners course slides using Flux Schnell GGUF."""
import json, urllib.request, urllib.error, time, os, sys

COMFY = "http://127.0.0.1:8188"
ASSETS = r"C:\AI presentations Output\ai-for-beginners\assets"
os.makedirs(ASSETS, exist_ok=True)

# ── Workflow template (Flux Schnell GGUF, 1280×720, 4 steps) ──
def build_workflow(prompt_text, seed, filename_prefix):
    return {
        "1": {"inputs": {"unet_name": "flux1-schnell-Q5_K_S.gguf"}, "class_type": "UnetLoaderGGUF"},
        "2": {"inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}, "class_type": "DualCLIPLoaderGGUF"},
        "3": {"inputs": {"guidance": 1.0, "conditioning": ["2", 0], "clip": ["2", 0], "text": prompt_text}, "class_type": "CLIPTextEncodeFlux"},
        "4": {"inputs": {"noise_seed": seed}, "class_type": "RandomNoise"},
        "5": {"inputs": {"steps": 4, "scheduler": "beta", "denoise": 1.0}, "class_type": "BasicScheduler"},
        "6": {"inputs": {"sampler": ["5", 0], "guider": ["3", 0], "noise": ["4", 0], "latent_image": ["7", 0]}, "class_type": "SamplerCustomAdvanced"},
        "7": {"inputs": {"width": 1280, "height": 720, "batch_size": 1}, "class_type": "EmptySD3LatentImage"},
        "8": {"inputs": {"samples": ["6", 0], "vae": ["9", 0]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"vae_name": "flux-vae-bf16.safetensors"}, "class_type": "VAELoader"},
        "10": {"inputs": {"images": ["8", 0], "filename_prefix": filename_prefix}, "class_type": "SaveImage"}
    }

# ── 9 Image prompts ──
IMAGES = [
    ("hero_bg", "dark atmospheric abstract neural network background, deep navy blue tones, glowing red accent streaks, floating geometric nodes and connections, futuristic AI technology atmosphere, cinematic moody lighting, no text no letters", 42),
    ("what_is_ai", "conceptual split composition: left side a cute golden retriever dog learning a trick with a treat, right side a mechanical calculator, divided by a soft gradient, educational diagram style, dark navy background, warm lighting, no text", 100),
    ("ai_vs_software", "two column comparison visual: left side an open recipe cookbook with precise instructions, right side a person learning to ride a bicycle through practice, conceptual, dark navy background with soft edges, educational, no text", 200),
    ("how_ai_learns", "three step progression illustration: step1 showing examples to someone, step2 a brain finding patterns with glowing connections, step3 a person improving at a skill like riding a bike, flowing left to right, dark navy background, warm accent colors, cinematic, no text", 300),
    ("gen_ai_showcase", "creative AI showcase: a robot artist painting colorful abstract art on a canvas, glowing creative energy, sparks of imagination, dark atmospheric background with deep navy, vibrant red and gold accent, magical atmosphere, no text", 400),
    ("ai_types", "three distinct symbolic icons in a row: a glowing cloud symbol left, a desktop computer symbol center, an autonomous robot symbol right, connected by subtle lines, dark navy background, clean modern tech style, red accent glow, no text", 500),
    ("ai_everywhere", "collage of AI applications: video camera icon, sound wave, medical cross, car steering wheel, art palette, all connected in a network pattern, dark navy background, subtle red accent, futuristic tech mood, no text", 600),
    ("try_it", "friendly inviting composition: an open laptop with a glowing chat interface, warm welcoming atmosphere, a hand reaching toward the screen, dark navy background, soft red accent glow, inviting and approachable, no text", 700),
    ("making_of", "behind the scenes creative process: three panels showing image generation, code writing, and text creation, flowing together into a final presentation on a TV screen, dark navy background, cinematic workflow visualization, no text", 800),
]

# ── Interrupt & clear ──
print("Clearing ComfyUI queue...")
for i in range(5):
    try:
        urllib.request.urlopen(urllib.request.Request(f"{COMFY}/interrupt", data=b"", method="POST"))
    except:
        pass
    time.sleep(0.3)
time.sleep(2)

results = []
for idx, (save_name, prompt, seed) in enumerate(IMAGES):
    filename_prefix = save_name.replace("_", "-")
    workflow = build_workflow(prompt, seed, filename_prefix)
    
    # Strip _-prefixed keys
    clean = {}
    for k, v in workflow.items():
        node = {nk: nv for nk, nv in v.items() if not nk.startswith("_")}
        clean[k] = node
    
    payload = json.dumps({"prompt": clean}).encode("utf-8")
    
    print(f"\n🎨 [{idx+1}/9] Generating: {save_name}.png (seed {seed})")
    print(f"   Prompt: {prompt[:90]}...")
    
    try:
        req = urllib.request.Request(f"{COMFY}/prompt", data=payload, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        prompt_id = resp.get("prompt_id")
        if not prompt_id:
            print(f"   ❌ No prompt_id: {resp}")
            results.append((save_name, None, "no prompt_id"))
            continue
        print(f"   ID: {prompt_id}")
    except Exception as e:
        print(f"   ❌ Submit failed: {e}")
        results.append((save_name, None, str(e)))
        continue
    
    # Poll (max 3 min)
    polled = 0
    image_file = None
    while polled < 36:
        time.sleep(5)
        polled += 1
        try:
            h = json.loads(urllib.request.urlopen(f"{COMFY}/history/{prompt_id}", timeout=5).read())
            if prompt_id in h:
                outputs = h[prompt_id].get("outputs", {})
                for node_id, node_output in outputs.items():
                    images = node_output.get("images", [])
                    if images:
                        img = images[0]
                        image_file = (img["filename"], img.get("subfolder", ""), img.get("type", "output"))
                        print(f"   ✅ Done in {polled * 5}s")
                        break
                if image_file:
                    break
        except Exception as e:
            print(f"   ⚠ Poll err: {e}")
    
    if not image_file:
        print(f"   ❌ Timed out")
        results.append((save_name, None, "timeout"))
        continue
    
    # Download
    filename, subfolder, img_type = image_file
    params = f"?filename={filename}&subfolder={subfolder}&type={img_type}"
    try:
        data = urllib.request.urlopen(f"{COMFY}/view{params}", timeout=30).read()
        clean_name = filename.replace("_00001_", "")
        dest = os.path.join(ASSETS, f"{save_name}.png")
        with open(dest, "wb") as f:
            f.write(data)
        print(f"   💾 {dest} ({len(data)//1024} KB)")
        results.append((save_name, dest, "ok"))
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        results.append((save_name, None, str(e)))

print("\n" + "=" * 60)
print("SUMMARY:")
ok = 0
for name, path, status in results:
    e = "✅" if status == "ok" else "❌"
    if status == "ok": ok += 1
    print(f"  {e} {name}: {status}")
print(f"\nDone: {ok}/{len(results)} images generated.")
