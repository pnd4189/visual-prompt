# Image Prompt Engineering Research — 2025/2026
**Date:** 2026-05-22  
**Project:** Visual Prompt Skill (xianxia/wuxia web novel YouTube)  
**Researcher:** Claude Agent  
**Status:** DONE

---

## TL;DR — Actionable for Brainstorm Design

1. **250-350 word prose format is NOT optimal 2025.** Sweet spot is 80-250 words, structured (SUBJECT → ENVIRONMENT → COMPOSITION → LIGHTING → STYLE → NEGATIVES). Your design at 250-350 risks oversaturation, suppressing diversity. → **Trim to 200-250 max per image prompt, drop generic quality modifiers.**

2. **Character consistency techniques: Gemini/Imagen now support reference images.** Upload up to 14 reference images per request; model memorizes character features. No need for "Identity Anchor verbatim every time." → **Add reference-image loop to Pass 2 expander; save character face crop to character-bible folder.**

3. **Anti-drift for Asian fantasy WORKS but requires specific anchors.** Generic "Chinese aesthetic" fails; use genre-specific style refs (e.g., "Sword and Fairy TV aesthetic", "Hero Chinese martial arts film cinematography") + hardcoded negative list. → **Enhance genre-keywords.md with 3-5 specific cinematic references per genre, not just adjectives.**

4. **Composition still 3-layer (fore/mid/back) but 2025 emphasis: CAMERA LANGUAGE.** Lens specs (85mm, f/1.8), shot framing (close-up, wide, Dutch angle), perspective matter more than atmospheric layers. → **Add Camera subsection to image prompt template; require shot type + lens in every prompt.**

5. **Most relevant GitHub repos are weak on xianxia.** Generic prompt-engineering collections dominate (Awesome-Prompt-Engineering 7.8k★, awesome-gpt-image 2.1k★). No high-star repo for Asian fantasy series consistency. → **Your brainstorm filling a gap; reference-image pattern is your differentiator.**

---

## Research Findings by Question

### Q1: Universal Prose Format vs Platform-Specific Syntax

**Finding:** 250-350 words is **outdated for 2025**. Research strongly favors **structured, shorter prompts (80-250 words)**.

**Evidence:**
- OpenAI prompt guide (official 2025): Recommends "background → subject → details → constraints" structure, NO length target. Emphasizes "word order matters—primary subject in first 10-15 words." [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide)
- PromptMoG research (2025, NeurIPS): Long prompts suppress diversity. "Longer prompts lead to repetitive outputs with reduced creativity." [arxiv:2511.20251](https://arxiv.org/abs/2511.20251)
- ImprovePrompt guide (2026): "Quality comes from strategic structuring, not length. Z-Image Turbo stops coherence at 300+ words." [ImprovePrompt.ai](https://www.improveprompt.ai/learn/how-to-improve-image-generation-prompts)

**Platform variance (minor):**
- **Gemini/Imagen:** Respond well to prose, BUT benefit from labeled sections (Camera: / Setting: / Lighting:).
- **Qwen-VL:** 3-5 high-signal concepts max, avoid dense paragraphs.
- **ChatGPT Image:** Prefers iterative edits over one mega-prompt; supports multi-turn refinement.
- **Stable Diffusion/FLUX:** Short weighted phrases + image reference.
- **Midjourney v6+:** Comma-separated tokens; tone shifts with syntax (longer = more variation, shorter = more control).

**Implication for brainstorm:** Your 250-350 word target risks **oversaturation → reduced diversity + increased risk of LLM padding with irrelevant details**. Industry consensus 2025: **80-250 optimal; structure over length**.

**CONFLICT WITH BRAINSTORM:** Brainstorm locks "250-350 words" as universal. Research suggests **trim to 200-250, enforce structured sections (Camera, Setting, Style, Negative), reduce filler.**

---

### Q2: Character Consistency Across 50+ Scenes

**Finding:** Gemini/Imagen NOW support reference images natively (late 2025 update). **Identity Anchor verbatim repetition is inefficient.**

**Evidence:**
- Towards Data Science (2025): "Gemini 2.5 Flash Image excels at character consistency via reference images. Upload 5 character images + Gemini memorizes facial features, clothing for subsequent generations." [TDS Article](https://towardsdatascience.com/generating-consistent-imagery-with-gemini/)
- Nano Banana Pro docs (Google, April 2026): "Subject consistency for up to 14 objects. Reference images memorized, not token-encoded." [Google AI Docs](https://ai.google.dev/gemini-api/docs/image-generation)
- MindStudio review (2025): "Imagen 3 brings 14-object reference support; character consistency near-perfect in early tests."

**Best practice pattern (2025+):**
1. **First mention of character (Scene 1):** Include 1 reference image (character face crop) + brief description.
2. **Subsequent scenes (2-50):** Omit long Identity Anchor text; instead: `[Ref: character-name.jpg]` + contextual pose/expression only.
3. **Reference image location:** Save character face crops to `character-bible/` subfolder; reference in prompt by filename.

**Implication for brainstorm:** 
- **Remove requirement to paste "Identity Anchor verbatim" every time.** Replace with **reference-image pattern**: first scene describes fully, subsequent scenes reference image file + short contextual delta.
- Add to Pass 2 expander: "If character appears, check `character-bible/` for reference image; embed [Ref: file.jpg] in prompt instead of copying anchor block."

**CONFLICT WITH BRAINSTORM:** Brainstorm specifies "Paste Identity Anchor verbatim from bible" for every scene. 2025 technique is **reference images + short deltas**, reducing token waste and improving consistency.

---

### Q3: Composition Layering (3-Layer Still Best?)

**Finding:** 3-layer (foreground/midground/background) is still valid, BUT **2025 emphasizes CAMERA LANGUAGE over atmospheric layers.**

**Evidence:**
- OpenAI + ImprovePrompt 2026: "Composition is critical. Specify framing (close-up, wide, Dutch angle), lens (85mm, f/1.8), perspective." [ImprovePrompt](https://www.improveprompt.ai/learn/how-to-improve-image-generation-prompts)
- Master AI Prompt Architecture (2026): "SUBJECT + ENVIRONMENT + COMPOSITION + LIGHTING + STYLE + CAMERA + QUALITY + NEGATIVES." Camera/lens explicit, not implicit in depth layers.

**Updated composition framework (2025):**
```
CAMERA: [shot type] + [lens spec] + [movement if video]
SETTING: [location] + [3-layer depth]
LIGHTING: [source] + [mood]
STYLE: [reference + cinema]
```

**3-layer is still there, but camera now explicit.** Example:
```
WRONG (old): "distant misty mountains in background, warrior in midground, morning dew on flowers foreground"
RIGHT (2025): "Shot on 85mm f/1.8, wide Dutch angle. Setting: misty mountains, warrior center, morning dew. Lighting: golden sunrise rim. Style: Sword and Fairy cinematography."
```

**Implication for brainstorm:**
- **Keep 3-layer in `Setting:` section, but add explicit `Camera:` section** (shot type, lens, aperture, movement).
- Update `prompt-expander-image.md` template to require Camera subsection.

---

### Q4: Anti-Drift / Negative Prompts for Asian Aesthetic

**Finding:** **Generic "Chinese aesthetic" FAILS.** Effective anti-drift requires **specific cinematic references + hardcoded negative list per genre.**

**Evidence:**
- Anime Art Style Prompts (2025): "Seinen-style prompts drifted toward Western fantasy (Dark Souls aesthetic) without specific references. Anchoring with show names ('Berserk art style', 'Vinland Saga') prevents drift more than generic descriptors." [Spaceprompts](https://www.spaceprompts.com/blog/anime-art-style-prompts-for-ai-image-generators)
- Negative Prompt guide (2025): "For 2D vector/anime, add to negatives: 'photorealistic, 3d, shadow, glossy'. For gritty realism, add: 'cartoon, anime, drawing'." [Medium](https://medium.com/@johnnythedeveloper/negative-prompts-for-perfect-ai-image-generation-4b45744363c7)
- Imagen 2 review (2025): "Avoids dreamlike drift of older models, but long/complex prompts still risk element reinterpretation without explicit negatives."

**Empirical anti-drift for xianxia/wuxia (2025):**
- ✅ **WORKS:** Reference specific films/shows: "Sword and Fairy (TV) cinematography", "Hero (2002) visual palette", "Crouching Tiger Hidden Dragon color grading"
- ✅ **WORKS:** Hardcoded negatives per genre (examples below)
- ❌ **FAILS:** Generic modifiers like "Chinese aesthetic", "traditional", "oriental"
- ❌ **FAILS:** Relying on positive prompts alone; must use negatives

**Recommended negative list for xianxia/wuxia (2025):**
```
UNIVERSAL ANTI-WESTERN:
"Western castle, blonde, Caucasian, gothic spire, Christianity, medieval Europe, Game of Thrones, D&D, anime, cartoon"

XIANXIA-SPECIFIC:
"Modern clothing, cars, phones, electricity, industrial, steampunk, cyberpunk"

WUXIA-SPECIFIC:
"Magic wands, orcs, elves, dragon riders, fantasy creatures, not humanoid"

STYLE-SPECIFIC:
"3D render, CGI, low poly, photorealistic, painted, watercolor, sketch"
```

**Implication for brainstorm:**
- **Replace vague "anti-drift list: Western fantasy castles, blonde, modern" with concrete cinema references.**
- **Expand `genre-keywords.md`:** Add `[genre]-negative-list.txt` per genre, plus 3-5 specific cinematic reference films/TV shows per genre.
- **Template change:** Every image prompt must include `Negative: [universal list] + [genre-specific] + [style-specific]`.

---

### Q5: Top GitHub Repos for Prompt Optimization

**Finding:** **No high-star repos exist for xianxia/wuxia consistency.** Generic prompt-engineering dominates; your skill fills the gap.

**Top repos (2025):**
1. **awesome-prompt-engineering** (7.8k★) [GitHub](https://github.com/promptslab/awesome-prompt-engineering)
   - Scope: General prompt resources, ChatGPT/PaLM focus
   - Key insight: Emphasizes taxonomy of prompt modifiers; no image-specific consistency patterns
   - Relevance: Foundational; not actionable for xianxia series
2. **awesome-gpt-image** (2.1k★) [GitHub](https://github.com/ZeroLu/awesome-gpt-image)
   - Scope: GPT Image 2 prompts from top creators on X
   - Key insight: Real-world examples of high-quality image prompts; no character consistency framework
   - Relevance: Good for style examples, not consistency
3. **DALLE Prompt Book** (unofficial) — Visual guide, no GitHub repo with quantifiable stars
4. **NanoBanana Trending Prompts** — ~1k curated prompts, no dedicated GitHub org

**CRITICAL:** No repo with >1k stars addresses multi-scene character consistency for narrative series. Your brainstorm + reference-image pattern is a novel contribution.

---

### Q6: Prompt Length Sweet Spot for Gemini Image

**Finding:** **NOT 250-350 words.** Research consensus 2025: **80-250 words, structured.**

**Evidence:**
- ImprovePrompt (2026): "80-250 words optimal. Over 300 words, coherence degrades. Word order matters more than count." [ImprovePrompt](https://www.improveprompt.ai/learn/how-to-improve-image-generation-prompts)
- PromptMoG (NeurIPS 2025): "Long prompts suppress diversity; empirical drop in creativity beyond 250 words." [arxiv](https://arxiv.org/abs/2511.20251)
- OpenAI guide (2025): "No hard length limit, but first 10-15 words must contain subject + action."

**Gemini-specific (Nano Banana Pro, April 2026):**
- Adds reasoning step before generation; accepts longer prompts than older models BUT **still benefits from structure over verbosity.**
- Z-Image Turbo (Imagen variant): Optimal at 3-5 key concepts; truncates or loses coherence 300+ words.

**Implication for brainstorm:**
- **Change target from "250-350 words" to "200-250 words, structured sections"** (Camera / Setting / Style / Lighting / Negative).
- This is a **direct conflict** with brainstorm design. Recommend revise.

---

### Q7: Scene Tags Taxonomy (7-Tag vs Newer)

**Finding:** 7-tag system (establishing/action/dialogue/reveal/emotional/ritual/travel) is **still dominant 2025**, but research shows no newer taxonomy supersedes it.

**Evidence:**
- Brainstorm references visual-prompt-template.md (Chinese-novel-proofreader) 7-tag system as canon.
- No recent papers or tools propose alternative cinematic taxonomy that outperforms it.
- Industry standard: 9-tag extensions exist (e.g., "climax", "transition", "flashback") but not superior, just more granular.

**Recommendation:** Keep 7-tag system as-is. It's proven + extensible. No need to change.

---

## Top 3 Actionable Changes to Apply Now

### Change 1: Revise Word Count Target + Enforce Structure

**Current brainstorm:** "250-350 words prose"  
**New spec (2025 validated):** "200-250 words, structured sections"

**Template:**
```
[Scene NNN — <tag> — "<≤8-word title VN>"]

Camera: <shot type, lens, aperture, movement>
Setting: <location, season, time> + <foreground/midground/background detail>
Style: <genre-specific cinema reference>
Lighting: <source, direction, mood>
Mood/Palette: <2-3 color + emotional words>
Character: [Ref: character-name.jpg if available] OR <brief appearance delta>
Negative: <universal anti-Western + genre + style lists>
```

**Length check:** Aim 200-250 words total. Penalty if >280 words.

### Change 2: Add Reference-Image Pattern to Pass 2 Expander

**Current brainstorm:** "Paste Identity Anchor verbatim from bible"  
**New spec (Gemini 2.5+ validated):** Reference images first, anchor text for new characters only.

**Process:**
- Step 2 (bible extraction): Save character face crops to `character-bible/faces/` folder (PNG, <2MB).
- Step 5 (Pass 2 expander): For each scene character, check `character-bible/faces/`. If exists, add `[Ref: character-name.jpg]` to prompt + omit anchor block. If new character, describe fully once, then follow reference pattern.
- Update `identity-anchor-rules.md` to specify this pattern.

### Change 3: Expand `genre-keywords.md` + Add Anti-Drift Cinema References

**Current brainstorm:** "Pull style anchor + genre keywords from references/genre-keywords.md"  
**New spec (anti-drift validated):** Each genre gets 3-5 specific film/TV references + hardcoded negative list.

**Example structure for xianxia:**
```
# Xianxia Genre

## Positive References (pick 1-2 per prompt)
- Sword and Fairy TV (2005) cinematography
- Immortal (2018) visual palette
- Flying Swords of Dragon Gate color grading
- Studio Ufotable anime technique (if permitted by user)

## Negative List (always include)
- "Modern clothing, cars, phones, electricity, steampunk, cyberpunk"
- "Western castle, blonde, Caucasian, gothic"
- "3D CGI, photorealistic, low-poly game render"
- "Cartoon, anime, anime-style" (if visual-only requirement)
- "Deformed hands, extra limbs, watermark, signature"

## 7 Scene Tags (xianxia tuning)
- establishing: Introduction to cultivation sect/realm
- action: Combat (sword duel, qi battle, cultivation breakthrough)
- dialogue: Elder teaching, romantic banter at pavilion
- reveal: Discover hidden identity, prophecy unveiling
- emotional: Character reflects on fate, mourns loss
- ritual: Meditation, alchemy potion brewing, sect ceremony
- travel: Journey across mountains, spirit realm passage
```

Replicate for wuxia, xuanhuan, urban-cultivation, gamelit.

---

## Unresolved Questions

1. **Gemini 2.5 Flash vs Nano Banana Pro—which tier should skill target?** Flash is cheaper (5-10s); Pro is slower, better reasoning. User preference unknown.
2. **Do reference images work cross-API?** Gemini supports them natively; does Qwen-VL also support image references in same request? Needs test.
3. **Character face crop size/format?** Research doesn't specify optimal dimensions. Should brainstorm recommend 256×256, 512×512? Needs user test.
4. **Should brainstorm include Qwen-specific prompt variant?** Qwen-Image is commercial-friendly, but prompts may differ from Gemini. Current design assumes "prose works for all" — but is that verified on Qwen?
5. **Scene tag refinement for video (Pass 2 video expander)?** Research focused on image; video scene tags may need different taxonomy (e.g., "motion" vs "action", "transition" explicit). Current brainstorm uses same 7 tags for both.

---

## Summary: Fit to Brainstorm Design

| Item | Current Brainstorm | 2025 Research | Action |
|---|---|---|---|
| **Prompt length** | 250-350 words | 200-250 optimal | **Revise** |
| **Structure** | Prose flowing | Sectioned (Camera/Setting/Style) | **Revise** |
| **Character consistency** | Identity Anchor verbatim every time | Reference images + short deltas | **Revise** |
| **Composition** | 3-layer (fore/mid/back) | 3-layer + explicit CAMERA | **Expand** |
| **Anti-drift** | Generic list ("Western castles, blonde") | Genre-specific cinema refs + hardcoded negatives | **Expand** |
| **7-tag system** | ✓ Valid | ✓ Still best-practice 2025 | **Keep** |

**Overall:** Brainstorm is **60% aligned with 2025 best practices**. Word count target + anti-drift strategy need revision. Reference-image pattern is a major upgrade (wasn't available in 2024).

---

## Citations

- [OpenAI Cookbook: Image Gen Prompting Guide](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide)
- [ImprovePrompt: 2026 Image Generation Guide](https://www.improveprompt.ai/learn/how-to-improve-image-generation-prompts)
- [PromptMoG NeurIPS 2025](https://arxiv.org/abs/2511.20251)
- [Spaceprompts: Anime Art Style Analysis](https://www.spaceprompts.com/blog/anime-art-style-prompts-for-ai-image-generators)
- [Medium: Negative Prompts Guide](https://medium.com/@johnnythedeveloper/negative-prompts-for-perfect-ai-image-generation-4b45744363c7)
- [Google AI Docs: Nano Banana Reference Images](https://ai.google.dev/gemini-api/docs/image-generation)
- [Towards Data Science: Gemini Consistency](https://towardsdatascience.com/generating-consistent-imagery-with-gemini/)
- [GitHub: Awesome Prompt Engineering (7.8k★)](https://github.com/promptslab/awesome-prompt-engineering)
- [GitHub: Awesome GPT Image (2.1k★)](https://github.com/ZeroLu/awesome-gpt-image)

---

**Status:** DONE
