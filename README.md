# Kunstmatige Intelligentie — Beginnersgids

16-slide Nederlandse AI-beginnerscursus (Reveal.js 5.x) voor familie-TV, desktop en mobiel.

## Bestand
- `ai-course.html` — de presentatie (open in browser of dubbelklik)
- `assets/` — 9 AI-gegenereerde achtergronden (1280×720, ComfyUI + Flux Schnell)

## Lokaal tonen
```bash
cd "C:\AI presentations Output\ai-for-beginners"
python -m http.server 8765
# open http://localhost:8765/ai-course.html
```

## Bediening
- Pijltjes / spatie / swipe = volgende
- `F` of de ⛶-knop rechtsboven = volledig scherm
- `Esc` = overzicht, `S` = speaker notes
- Werkt met TV-afstandsbediening (D-pad pijltjes)

## Wat is gefixt (vs. DeepSeek-versie)
De oude versie liet tekst buiten beeld vallen (titel afgekapt aan de bovenkant).
Oorzaak: `center:false` + content hoger dan het 720px-canvas → spill.

Oplossing:
- Elke `<section>` is vergrendeld op exact **1280×720** met `display:flex`,
  `justify-content:center` en `overflow:hidden` → niets kan meer buiten beeld vallen.
- Reveal config op `center:true` met `margin:0.04`.
- Image-layouts: `max-height:460px`, `object-fit:contain` zodat beelden nooit afgekapt worden.
- Kaarten op `flex:1 1 0` zodat 4 kaarten altijd op één rij passen.
- Slide 12 omgezet naar 2-koloms layout om verticale overflow te voorkomen.

Extra flash:
- Animated gradient-accentbalk links op elke slide
- Zwevende glow-blob (floatGlow animatie)
- Gradient-tekst op titels ("Kunstmatige Intelligentie", "Bedankt!", "AI is het NU.")
- Hover-lift op kaarten en badges
- Auto-Animate tussen de 3 "Hoe Leert AI"-stappen
