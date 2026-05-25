# Scene Tag → Camera Mapping

> Related: [[visual-prompt-template]] · [[youtube-pacing-guide]]

When the scene planner classifies each scene with a tag, use this table to
pick the default shot type, lens, and camera movement for the Cinematography
(video) and Camera (image) section. Override only if the chapter text
explicitly demands a different shot.

## Mapping Table

| Scene Tag | Shot Type | Lens (mm) | Camera Movement | When to use |
|---|---|---|---|---|
| **establishing** | Wide / extreme wide | 24mm | Slow push-in or static | Open chapter; new location; reveal a landscape, sect compound, city |
| **action** | Medium-wide tracking | 35mm | Handheld follow with motion blur | Duels, chases, escapes, combat |
| **dialogue** | Medium two-shot OR shot-reverse-shot | 50mm | Static / slight handheld breath | Two characters talking face to face |
| **reveal** | Medium close-up → wide | 50mm zoom OR 35mm dolly back | Slow pull-out or rapid push-in | Big reveal: identity, artifact, true power |
| **emotional** | Close-up | 85mm | Static, slight rack focus | Inner moment, grief, decision, breakthrough |
| **ritual** | Symmetrical medium-wide | 35mm | Static centered OR slow orbital | Cultivation, pill forging, ceremony, breakthrough |
| **travel** | Wide tracking | 28mm | Lateral tracking OR slow aerial | Montage of journey, mountain pass, riding |

## Notes

- **Image prompts** also use this — translate `Camera Movement` to the
  implied static frame (e.g., "tracking" → "frozen mid-motion with motion-blur
  hint on background").
- **Aspect ratio:** always 16:9 unless user explicitly overrides.
- **For 8-second videos:** the camera movement column is the SUSTAINED
  movement across all 3 beats — don't change shot type mid-clip (Veo3 handles
  one camera move per clip cleanly; multi-cut clips look glitchy).
