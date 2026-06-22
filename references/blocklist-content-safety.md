# Content-Safety Blocklist — data for `scripts/check_content_safety.py`

> Related: [[visual-prompt-template]] · [[negative-lists]] · [[style-catalog]]

The deterministic content-safety gate parses this file. Each `## SECTION` is one
blocked category. Lines under a section follow two conventions:

- **plain line** = a literal token, matched **case-insensitive, whole-word**.
- **`re: <pattern>`** = a Python regex (already includes its own flags/anchors).

Blank lines and `<!-- comment -->` lines are ignored. The list is curated and
extensible, NOT exhaustive — add tokens as new violations surface.

Fix behavior per section (see the script): BRANDS / IP_CHARACTERS / LIKENESS are
stripped; GORE → `no graphic blood`; SEXUAL → `modestly clothed`;
PHOTOREAL_VIDEO → `stylized animation`; RELIGION_HIGH_RISK is **WARN-only**
(never auto-rewritten — context cannot be judged by regex).

---

## BRANDS
Nike
Adidas
Puma
Reebok
Apple
iPhone
iPad
Samsung
Galaxy
Huawei
Xiaomi
Coca-Cola
Coca Cola
Pepsi
Starbucks
McDonald's
McDonalds
KFC
Louis Vuitton
Gucci
Prada
Chanel
Versace
Rolex
Ferrari
Lamborghini
Tesla
Disney
Pixar
Marvel
DC Comics
Nintendo
PlayStation
Xbox
Genshin Impact
Honkai
Pokemon
Pokémon
Coca
Supreme

## IP_CHARACTERS
Naruto
Sasuke
Goku
Vegeta
Luffy
Pikachu
Mickey Mouse
Donald Duck
Iron Man
Spider-Man
Spiderman
Batman
Superman
Elsa
Harry Potter
Darth Vader
Mario
Sonic the Hedgehog
Hatsune Miku

## LIKENESS_TRIGGERS
re: (?i)\b(?:looks like|resembles|in the style of|cosplay of|portrait of|modeled on|giống|trông giống|theo phong cách|mô phỏng)\b\s+["']?[A-ZÀ-Ỹ][\wÀ-ỹ.'-]+(?:\s+[A-ZÀ-Ỹ][\wÀ-ỹ.'-]+)*

## GORE
re: (?i)\b(decapitat\w*|disembowel\w*|dismember\w*|eviscerat\w*|entrails|gushing blood|blood splatter|blood spurt\w*|mutilat\w*|tortur\w*|gore)\b
máu me
chặt đầu
moi ruột
phanh thây
xẻ thịt

## SEXUAL
re: (?i)\b(nude|naked|nudity|topless|bottomless|sexual|erotic|lingerie|cleavage|seductive|provocative|fetish)\b
khỏa thân
hở hang
gợi dục
khiêu dâm
dâm dục

## RELIGION_HIGH_RISK
<!-- WARN-only: never auto-rewritten; flags real-religion depiction/desecration -->
Prophet Muhammad
Muhammad
Jesus Christ
re: (?i)\b(desecrat\w*|blasphem\w*|burning (?:the )?(?:quran|koran|bible|torah))\b

## PHOTOREAL_VIDEO
<!-- #8 video animation-only: ban live-action / real-human realism. Must NOT match
     painterly catalog words "semi-realistic", "photo-real lighting", "realistic textures". -->
re: (?i)\b(live[- ]action|photoreal(?:istic)? (?:footage|video|render)|hyper[- ]?realistic|real human (?:actor|face|skin)|filmed (?:footage|scene)|deepfake|DSLR photo|8k photograph)\b
