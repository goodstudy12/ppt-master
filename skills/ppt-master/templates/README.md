# Template Resources

## Design Specification & Outline Reference

`design_spec_reference.md` is an all-in-one reference template for defining:
1.  **Visual Specifications**: Canvas dimensions, color scheme, typography, layout principles
2.  **Content Outline**: Slide-by-slide page structure planning
3.  **Technical Constraints**: Hard requirements for SVG generation and PPT compatibility

[View Design Spec Reference](./design_spec_reference.md)

## Page Layout Templates

The `layouts/` directory contains the retained FanRuan style layout template:

- **FanRuan Tech**: light blue enterprise BI / dashboard / report designer style

- **Human browsing**: [layouts/README.md](./layouts/README.md)
- **Slim lookup (discovery only)**: [layouts/layouts_index.json](./layouts/layouts_index.json) — used to answer "what templates exist?". Step 3 triggers on an explicit directory path supplied by the user, not on names from this index.

## Brand Identity Presets

The `brands/` directory is currently empty by design. This repository keeps only the FanRuan style theme under `layouts/fanruan_tech/`; brand-only presets were removed from the active library.

A future FanRuan-only brand preset may be added through the brand workflow, but non-FanRuan brand presets should not be registered here.

- **Human browsing**: [brands/README.md](./brands/README.md)
- **Discovery index (no trigger)**: [brands/brands_index.json](./brands/brands_index.json) — answers "what brands exist?"; Step 3 still requires an explicit directory path from the user
- **Creation workflow**: [`../workflows/create-brand.md`](../workflows/create-brand.md)

## Visualization Templates

The `charts/` directory contains 57 standardized visualization templates. For backward compatibility, the directory name remains `charts/`, but its scope includes charts, infographics, process diagrams, relationship diagrams, strategic frameworks, and system architecture diagrams:

- KPI Cards
- Bar Chart / Stacked Bar Chart
- Line Chart / Dual-Axis Line Chart
- Donut Chart
- Radar Chart
- Funnel Chart
- Matrix (2x2)
- Timeline
- Gantt Chart
- Process Flow
- Org Chart
- Layered Architecture / Module Composition / Hub with Described Spokes / Pipeline with Stages / Client-Server Flow

- **Library index (single source of truth)**: [charts/charts_index.json](./charts/charts_index.json)
- **Directory overview**: [charts/README.md](./charts/README.md)

## Icon Library

The `icons/` directory contains 11,600+ vector icons across five libraries:

| Library | Style | Count |
|---------|-------|-------|
| `chunk-filled` | fill / straight-line geometry | 640 |
| `tabler-filled` | fill / bezier-curve forms | 1000+ |
| `tabler-outline` | stroke / line | 5000+ |
| `phosphor-duotone` | duotone / single color + 0.2 opacity backplate | 1200+ |
| `simple-icons` | brand logos (company / product marks) | 3400+ |

- **Usage & style rules**: [icons/README.md](./icons/README.md)
- **Search icons**: `ls skills/ppt-master/templates/icons/<library>/ | grep <keyword>`
