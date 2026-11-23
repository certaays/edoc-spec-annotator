# edoc-spec-annotator

Convert electronic document (e-doc) PDFs into page images, analyze form fields using customizable bridging and UI rules, and render red-pen requirement annotations (*coretan*) directly onto the pages. Each analysis is stored as a revisable JSON spec so requirements can be tweaked in seconds and exported as annotated PNGs and PDFs for programmers.

## How It Works

1. **PDF → Images (`pdftoppm`)**: Renders each PDF page into PNGs inside `pages/<slug>/`.
2. **Analyze (`SKILL.md` → JSON)**: Classifies fields using the rules in [`.agents/skills/edoc-analysis/SKILL.md`](.agents/skills/edoc-analysis/SKILL.md) and writes a coordinate spec (`0–1000` normalized) to `annotations/<slug>.json`.
3. **Render (*Coretan*)**: [`scripts/render_analysis.py`](scripts/render_analysis.py) draws red rectangles and labels onto the page images and outputs annotated PNGs + a combined PDF into `output/<slug>/`.
4. **Archive**: Processed PDFs are moved from `input/` to `analyzed/` so they are not re-analyzed automatically.

## Folder Structure

```text
.
├── .agents/skills/edoc-analysis/
│   └── SKILL.md                # Classification rules & workflow instructions
├── input/                      # Drop new (unanalyzed) PDFs here
├── analyzed/                   # Processed PDFs moved here after analysis
├── pages/<slug>/               # Raw PNG pages per document
├── annotations/<slug>.json     # Revisable JSON annotation specs
├── output/<slug>/              # Annotated PNGs & combined PDF per document
└── scripts/
    └── render_analysis.py      # Red-pen overlay renderer
```

## Prerequisites

- Python 3.10+ with `Pillow` (`PIL`)
- `poppler-utils` (`pdftoppm`)

## Usage

### 1. Analyze a New PDF (with AI Agent / Skill)
1. Drop your PDF into `input/`.
2. Ask your agent to analyze it—the `edoc-analysis` skill will convert it to PNGs, generate `annotations/<slug>.json`, render `output/<slug>/`, and move the source PDF to `analyzed/`.

### 2. Render Manually from a JSON Spec
```bash
python3 scripts/render_analysis.py annotations/<slug>.json
```

This generates:
- `output/<slug>/<slug>_page_<n>_annotated.png`
- `output/<slug>/<slug>_annotated.pdf`

### 3. Revise Annotations
Edit any label, box, or position in `annotations/<slug>.json` (or ask the agent to revise a specific field) and re-run:
```bash
python3 scripts/render_analysis.py annotations/<slug>.json
```

## Default Field Rules

| Document Element | Annotation Label |
| :--- | :--- |
| Patient identity (`Nama`, `No. RM`, `Tgl. Lahir`, `Alamat`, etc.) | `bridging data pasien` |
| Vital signs (`T`, `N`, `S`, `RR`, `GCS`, `SPO2`, etc.) | `bridging TTV` |
| Diagnosis fields | `bridging diagnosa + tambah data` |
| Procedures (`Tindakan`) | `bridging tindakan` |
| Staff / clinician fields (`Dokter`, `Perawat`, `Petugas`) | `autocomplete nakes` |
| Signature blocks (`TTD`) | `TTD QR + autocomplete nakes` |
| Short blank / dotted line | `freetext` |
| Multi-line / large blank box | `text area` |
| Date / time fields | `input tgl` / `input jam` / `input tgl dan jam` |
| Checkboxes | `checkbox single option` / `checkbox multiple select` |
| Checkbox + follow-up text input | `1. checkbox ...` / `2. input text disable enable` |

To add more bridging types or customize rules, edit [`.agents/skills/edoc-analysis/SKILL.md`](.agents/skills/edoc-analysis/SKILL.md).

