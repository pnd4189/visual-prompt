# Negative Lists — Anti-Drift Guard

> Related: [[visual-prompt-template]] · [[genre-keywords]] · [[style-catalog]]

Five-layer negative prompt construction. Append all five layers to the
`Negative:` section of every image prompt. For Veo3 videos: embed inline in
Style & Ambiance ("avoiding X, X, X") since Veo3 ignores standalone negative
sections.

**Max 28 items total** across all 5 layers (token budget): 10 + 5 + 5 + 4 + 4.

---

## Layer 1 — Universal Anti-Western (always include, 10 items)

```
no medieval European armor, no winged dragons, no gothic cathedral,
no blonde hair as default, no blue eyes as default, no Renaissance fair costume,
no fur cloaks, no Viking horns, no celtic knotwork, no crusader cross
```

These items prevent the model from defaulting to Western fantasy when given
generic prompts like "warrior" or "magician."

---

## Layer 2 — Genre-Specific (choose ONE block, 5 items)

### Tiên hiệp / Huyền huyễn
```
no jeans, no sneakers, no glasses, no neon lighting, no automatic firearms
```

### Võ hiệp
```
no magic energy explosions, no glowing fist auras, no flying swords mid-air,
no qi shockwaves, no levitation
```

### Đô thị (modern)
```
no cultivation sect robes, no straw sandals, no Tang dynasty armor,
no jade hairpins as everyday wear, no Wuxia-era weapons in modern hands
```

### Cổ điển (historical, no magic)
```
no glowing energy effects, no flying characters, no magical formations,
no qi visualizations, no cultivation auras
```

---

## Layer 3 — AI Artifact Defense (always include, 5 items)

```
no logo, no watermark, no text overlay, no distorted hands, no extra fingers
```

---

## Layer 4 — Likeness / Copyright Safety (always include, 4 items)

```
no copied web image, no celebrity face, no known-character likeness,
no exact branded costume
```

These items prevent the model from cloning a public figure, internet image, or
recognizable copyrighted character design. Use original faces from the character
bible and original costumes from the story context.

---

## Layer 5 — Style Negatives (from active style, 4 items)

Take the first **4** items from the `style negatives` field of the chosen style
entry in `.work/active-style.md` (materialized from [[style-catalog]]). These
keep the render from drifting away from the selected art style.

Example (style = `donghua-xianxia`):
```
no live-action photographic skin, no muted live-action desaturation,
no Western 3D cartoon proportions, no claymation
```

If the entry lists fewer than 4, use all of them.

---

## Composed Example (xianxia scene, style = donghua-xianxia)

```
Negative: no medieval European armor, no winged dragons, no gothic cathedral,
no blonde hair as default, no blue eyes as default, no Renaissance fair
costume, no fur cloaks, no Viking horns, no celtic knotwork, no crusader
cross, no jeans, no sneakers, no glasses, no neon lighting, no automatic
firearms, no logo, no watermark, no text overlay, no distorted hands,
no extra fingers, no copied web image, no celebrity face, no known-character
likeness, no exact branded costume, no live-action photographic skin,
no muted live-action desaturation, no Western 3D cartoon proportions, no claymation
```

Exactly 28 items (10 + 5 + 5 + 4 + 4). Comma-separated. Single line in the prompt's
Negative section. The last 4 (Layer 5) come from `.work/active-style.md` and change
with the chosen style. DALL-E paste: convert to "avoiding X, X, X" in the Style line.
