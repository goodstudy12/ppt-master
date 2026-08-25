# Renderings — Index

A **rendering** is a visual style family: line quality, texture, depth, material, mood. Lock one rendering per deck — every AI image in the deck shares it.

> **HEX values are not in renderings.** Rendering describes how the image is drawn. The new flow starts from the deck's core color anchors in `spec_lock.md colors` and interprets them with the Design Spec/image context; it does not ask for or author a separate image palette. See [`image-generator.md`](../image-generator.md) §2.

> **Core deck identity has precedence.** Any sample HEX inside an individual rendering file is illustrative legacy prose. Prompt assembly replaces identity roles with the current deck anchors, then may derive coherent tints, light/shadow transitions, material colors, and atmospheric hues from the rendering and image context. Do not replace the deck identity with an unrelated palette. When one derived tone becomes a reusable semantic role across images/pages, promote it to a named lock row.

---

## 1. Catalog (20 renderings)

Each rendering keeps its own authoritative file with: style paragraph, line / texture / depth notes, deck HEX usage, and a fewshot prompt snippet. Read this index alone while choosing a direction. Only after a preset or custom bases are fixed may the active role read the selected sibling files: one file for a preset, every exact `image_rendering_references` file for a catalog-based custom, and none for a novel custom. Never glob the directory or read an unselected sibling. Whether AI imagery is recommended remains a separate source decision; Image_Generator follows the same selected-only rule.

### 1.1 Modern / commercial (the corporate-PPT main field)

| Rendering | One-liner | Typical image job |
|---|---|---|
| [`vector-illustration`](./vector-illustration.md) | Clean flat vector with bold shapes, no gradients | Consulting / SaaS / general professional decks |
| [`flat`](./flat.md) | Modern geometric blocks, slightly more design-forward than vector | Brand / product showcase decks |
| [`minimalist-swiss`](./minimalist-swiss.md) | Swiss-grid Bauhaus austerity, aggressive whitespace | High-end consulting / architecture / luxury / type foundries |
| [`glassmorphism`](./glassmorphism.md) | Frosted-glass translucent panels, soft shadows | Modern SaaS / fintech / health-tech / premium apps |
| [`3d-isometric`](./3d-isometric.md) | Isometric 3D forms with subtle shadows | Tech architecture / product structure |
| [`digital-dashboard`](./digital-dashboard.md) | Polished UI / data-viz aesthetic | SaaS demos / data products |
| [`corporate-photo`](./corporate-photo.md) | Editorial photography, real subjects | Team / lifestyle / product shots |
| [`blueprint`](./blueprint.md) | Technical schematic with grid, monospace cues | Architecture / engineering / AI systems |
| [`editorial`](./editorial.md) | Magazine-style infographic look | Finance / journalism / explainers |

### 1.2 Hand-drawn / educational

| Rendering | One-liner | Typical image job |
|---|---|---|
| [`sketch-notes`](./sketch-notes.md) | Warm cream paper, black hand-drawn lines, pastel fills | Education / training / onboarding |
| [`ink-notes`](./ink-notes.md) | Pure white, black ink, sparse semantic color | Methodology / Before-After / manifestos |
| [`chalkboard`](./chalkboard.md) | Chalk on board, classroom feel | Teaching / tutorials / classroom decks |
| [`paper-cut`](./paper-cut.md) | Layered paper craft, scissor-cut edges, soft shadows | Education / children / cultural / festival / sustainability |

### 1.3 Narrative / atmospheric

| Rendering | One-liner | Typical image job |
|---|---|---|
| [`watercolor`](./watercolor.md) | Painterly soft edges, color bleeding | Illustrative lifestyle / travel story / brand story |
| [`warm-scene`](./warm-scene.md) | Golden-hour cinematic warmth | Personal growth / origin story |
| [`screen-print`](./screen-print.md) | Halftone poster art, 2-5 flat colors | Cultural / media / cinematic covers |
| [`vintage-poster`](./vintage-poster.md) | Mid-century modern poster, halftone + paper grain | Cultural retrospective / brand heritage / historic hospitality identity / anniversaries |

### 1.4 Specialty

| Rendering | One-liner | Typical image job |
|---|---|---|
| [`fantasy-animation`](./fantasy-animation.md) | Ghibli/Disney hand-drawn warmth | Children / storybook / brand fable |
| [`pixel-art`](./pixel-art.md) | 8-bit retro game aesthetic | Gaming / retro tech / nostalgic |
| [`nature`](./nature.md) | Organic earthy illustration | Environment / wellness / sustainability |

### 1.5 Editable `custom` projection

Every coordinated Stage-2 direction carries one complete `rendering: custom` candidate even when `recommend.image_usage` does not include `ai`. The UI keeps rendering controls hidden until the current source selection includes AI, then exposes the three already-authored project candidates without another backend recommendation. `custom` is not constrained by its relationship to the catalog: it may use catalog material in any way or none, including carrying one fitting preset treatment unchanged. The three complete directions are plainly different designs, but no single component is required to carry that difference: rendering treatments and bases may coincide when other components express it, while a different name, note, or reference count alone is never a difference. The 20 fixed renderings remain lower-level single-select alternatives. A template-backed proposal must honor inherited identity and the confirmed template-application plan.

**Hard rule — `rendering_behavior` prose**:

| Rule | Value |
|---|---|
| Length | One paragraph, 2-5 sentences |
| Axes covered | line / texture / depth / material / mood (same as preset files) |
| Catalog basis | Freeze every exact id from this index, then read only those files before applying one basis or synthesizing several |

```yaml
- image_rendering: custom
- image_rendering_behavior: "Hand-screened poster aesthetic — slightly misregistered halftone overlays, 3 flat ink colors with visible dot pattern at 12% opacity, no gradients, no anti-aliased edges; reads as silkscreen print."
```

**Hard rule**: three complete rendering candidates are mandatory in every fresh Stage-2 direction set; AI source recommendation remains independent. See [`strategist-image.md`](../strategist-image.md) for the Stage-2 carrier and downstream lock behavior.

Write `image_rendering_references` only when the confirmed custom direction actually uses catalog material. One rendering may supply the complete treatment unchanged; when several are named, each contributes a distinct executable job across line, texture, depth, material, or mood. Reference count has no fixed cap; count is an outcome, not a target. A four-basis direction may assign `vector-illustration` to silhouette clarity, `minimalist-swiss` to negative-space composition, `screen-print` to restrained halftone texture, and `warm-scene` to light and mood; list all four ids. Omit every rendering whose contribution cannot be stated and never add a second merely to imply synthesis. A custom using no catalog source omits the field and proceeds from its standalone behavior; never invent a reference merely to legitimize `custom`.

---

## 2. Selection Boundary

**Reference — not a constraint**: Resolve the intended image jobs and visual
style before choosing. Compare every catalog row through the image's required
line quality, texture, depth, material, mood, documentary identity, and role in
the page. A topic or industry keyword never selects the deck-wide rendering or
turns a named real-world subject into an AI row. A paired visual-style
rendering is one coherence candidate, not a default answer. When no preset
describes the intended treatment, use `custom` per §1.5.

| `d. Style` signal | Recommended rendering | Alternates |
|---|---|---|
| FanRuan BI dashboard / FineReport / FineBI | `digital-dashboard` | `blueprint`, `vector-illustration` |
| Operating report / management cockpit / KPI monitoring | `digital-dashboard` | `corporate-photo`, `flat` |
| Enterprise digitalization / data analysis report | `blueprint` or `digital-dashboard` | `vector-illustration`, `flat` |
| Strategic / MBB / board | `editorial` or `vector-illustration` | `blueprint`, `minimalist-swiss` |
| Corporate report / analysis | `vector-illustration` | `flat`, `digital-dashboard` |
| High-end consulting / luxury / 高端 / design-firm | `minimalist-swiss` | `editorial`, `vector-illustration` |
| Tech / SaaS / AI / system / architecture | `3d-isometric`, `blueprint`, or `digital-dashboard` | `flat`, `vector-illustration` |
| Modern SaaS / fintech / health-tech / premium app | `glassmorphism` | `digital-dashboard`, `flat` |
| Product launch / brand / marketing | `flat`, `3d-isometric`, or `corporate-photo` | `vector-illustration` |
| Education / training / onboarding / 教学 | `sketch-notes` | `vector-illustration` (if school is corporate), `paper-cut` |
| Children / story / storybook / 儿童 | `fantasy-animation` | `paper-cut`, `watercolor`, `sketch-notes` |
| Cultural / folk / festival / 文化 / 节日 | `paper-cut` | `vintage-poster`, `screen-print` |
| Methodology / Before-After / manifesto / 方法论 | `ink-notes` | `editorial` |
| Government / formal / official report | `editorial` or `corporate-photo` | `vector-illustration` |
| Finance / data journalism / 财经 | `editorial` or `digital-dashboard` | `vector-illustration` |
| Personal story / 个人成长 / lifestyle | `watercolor`, `warm-scene` | `corporate-photo`, `paper-cut` |
| Cultural / media / opinion / cinematic | `screen-print`, `vintage-poster` | `editorial`, `warm-scene` |
| Brand heritage / hospitality / 老字号 / 周年 | `vintage-poster` | `screen-print`, `editorial` |
| Gaming / retro / 8-bit / 复古 | `pixel-art` | `vintage-poster` |
| Environment / wellness / 环保 / 户外 | `nature` | `watercolor`, `paper-cut` |
| Classroom / blackboard / 课堂 | `chalkboard` | `sketch-notes` |
| Team / company / product photo | `corporate-photo` | — |

---

## 3. How to use

1. Read the resolved visual system and the deck's intended AI image jobs.
2. Compare the complete catalog and choose the strongest whole-deck fit, or use a warranted `custom` treatment.
3. For a preset, read `image-renderings/<chosen>.md`. For `custom`, read every file named in `image_rendering_references`: apply one basis under the confirmed behavior, or synthesize several by their stated contributions. With no references, use the behavior directly. Apply the result when assembling prompts per [`image-generator.md`](../image-generator.md) §4.

**Lock for the whole deck.** Don't change rendering between images in the same deck.
