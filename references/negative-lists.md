# Negative Lists — Anti-Drift Guard

> Related: [[visual-prompt-template]] · [[genre-keywords]]

Three-layer negative prompt construction. Append all three layers to the
`Negative:` section of every image prompt. For Veo3 videos: embed inline in
Style & Ambiance ("avoiding X, X, X") since Veo3 ignores standalone negative
sections.

**Max 20 items total** across all 3 layers (token budget).

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

## Layer 3 — Style / AI Artifact Defense (always include, 5 items)

```
no logo, no watermark, no text overlay, no distorted hands, no extra fingers
```

---

## Composed Example (xianxia scene)

```
Negative: no medieval European armor, no winged dragons, no gothic cathedral,
no blonde hair as default, no blue eyes as default, no Renaissance fair
costume, no fur cloaks, no Viking horns, no celtic knotwork, no crusader
cross, no jeans, no sneakers, no glasses, no neon lighting, no automatic
firearms, no logo, no watermark, no text overlay, no distorted hands,
no extra fingers
```

Exactly 20 items. Comma-separated. Single line in the prompt's Negative
section. DALL-E paste: convert to "avoiding X, X, X" in the Style line.
