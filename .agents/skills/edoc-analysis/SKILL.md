---
name: edoc-analysis
description: >-
  Analyze electronic document (e-doc) PDFs to generate programmer requirement
  and API bridging annotations ("coretan"). Converts PDFs to PNGs, classifies
  fields using standard bridging/UI rules, outputs a revisable JSON spec, and
  renders red-pen rectangles and labels onto the document pages.
---

# E-Doc Analysis & Bridging Annotator

Use this skill whenever the user wants to analyze a hospital/electronic document PDF, revise an existing annotation spec, or render programmer requirement overlays.

## Workspace Layout

- `input/` — Drop **new** (unanalyzed) e-doc PDFs here
- `analyzed/` — Completed source PDFs are moved here after analysis so `input/` stays clean
- `pages/<slug>/` — Raw PNG pages rendered from each PDF via `pdftoppm`
- `annotations/<slug>.json` — Revisable JSON specs using `0–1000` normalized coordinates
- `output/<slug>/` — Annotated PNGs (`<slug>_page_<n>_annotated.png`) and combined PDF (`<slug>_annotated.pdf`)
- `scripts/render_analysis.py` — Renderer that draws red rectangles and labels from JSON

## Workflow

> **Never re-analyze past PDFs automatically.** Only process PDFs currently in `input/` that do not already have an `annotations/<slug>.json` (unless the user explicitly asks to re-analyze).

### 1. Convert PDF to Images
Create a subfolder in `pages/` and run `pdftoppm` at 150 DPI:
```bash
mkdir -p pages/<slug>
pdftoppm -png -r 150 "input/<file.pdf>" pages/<slug>/page
```

### 2. Inspect Pages & Write `annotations/<slug>.json`
Inspect each generated PNG and map every field/section using `0–1000` normalized coordinates (`[x1, y1, x2, y2]` for boxes, `[x, y]` for label positions).

#### Default Classification Rules
Apply these standard programmer specs unless the user specifies otherwise:

- **Patient Identity** (`Nama`, `No. RM`, `Tgl. Lahir`, `Jenis Kelamin`, `Alamat`, `NIK`, `No. Kartu`, `No. SEP`, `Tgl. Masuk`, `Tgl. Pulang`):
  - Group in a red rectangle → `bridging data pasien`
- **Vital Signs / TTV** (`Tanda Vital`, `Tekanan Darah`, `Nadi`, `Suhu`, `Nafas`, `RR`, `GCS`, `SPO2`, `Berat Badan`, `Tinggi Badan`, `Kondisi pasien`):
  - Group in a red rectangle → `bridging TTV`
- **Diagnosis** (`Diagnosis`, `Diagnosa Pra Bedah`, `Diagnosa Pasca Bedah`):
  - Label → `bridging diagnosa + tambah data` (or `bridging diagnosa` if read-only)
- **Procedures** (`Tindakan`, `Nama / Macam Operasi / Tindakan Pembedahan`):
  - Label → `bridging tindakan`
- **Staff / Healthcare Workers (`Nakes`)**:
  - Name/role field (`Dokter Operator`, `Asisten`, `Perawat`, `Dokter Anestesi`, `Petugas`) → `autocomplete nakes`
  - Signature block (`TTD`, `Tanda tangan`, `Petugas Rujuk`, `Petugas Penerima`) → `TTD QR + autocomplete nakes`
- **Dates & Times**:
  - Date only (`Tanggal Pembedahan`) → `input tgl`
  - Time only (`Pembedahan mulai`, `Pembedahan Selesai`) → `input jam`
  - Date & time (`Tanggal dan jam ...`) → `input tgl dan jam`
- **Text Inputs**:
  - Short inline blank / dotted line (`.....`) → `freetext`
  - Large blank box / multi-line section (`Terapi`, `Laporan Operasi`, `Instruksi`, `Temuan`) → `text area`
- **Checkboxes (`☐`)**:
  - Mutually exclusive choices → red rectangle around options + `checkbox single option`
  - Multiple choices allowed → red rectangle around options + `checkbox multiple select`
  - Checkbox paired with a follow-up text input (`Lainnya: ....`, `No Hp: ....`) → red rectangle + numbered label:
    `1. checkbox single option` (or `multiple select`)\n`2. input text disable enable`

#### Visual Placement Rules
- Use red (`#D92B2B`) rectangles around grouped fields and checkbox blocks.
- Place red labels in empty whitespace inside the field box, over dotted lines, or in the adjacent margin—never obscure printed field names.
- Keep labels concise and directly readable by a programmer.

#### JSON Schema (`annotations/<slug>.json`)
```json
{
  "doc_name": "RS53_RM17.4",
  "pages": [
    {
      "image": "pages/RS53_RM17.4-1.png",
      "annotations": [
        {
          "id": "patient_identity",
          "box": [512, 18, 920, 118],
          "label": "bridging data pasien",
          "label_pos": [760, 88],
          "anchor": "mm",
          "font_size": 16
        }
      ]
    }
  ]
}
```
- `box` is optional (omit for standalone labels like `freetext` or `text area`).
- `label` is optional (omit for box-only highlights).
- `anchor` supports Pillow anchors (`lt`, `lm`, `mm`, `rt`, etc., default `"lt"`).
- `bg`: optional `true` to draw a subtle white backing behind text when placed over dotted lines.

### 3. Render Annotated Outputs
Run:
```bash
python3 scripts/render_analysis.py annotations/<slug>.json
```
This writes annotated PNGs and a combined `<slug>_annotated.pdf` into `output/<slug>/`.

### 4. Move Processed PDF to `analyzed/`
After rendering succeeds, move the source PDF out of `input/` so it is not re-processed later:
```bash
mkdir -p analyzed && mv "input/<file.pdf>" analyzed/
```

### 5. Revising via Prompt
When the user asks to change a field (e.g., *"change RS Tujuan from freetext to dropdown"* or *"make checklist single select"*):
1. Edit only the matching item in `annotations/<slug>.json`.
2. Re-run `python3 scripts/render_analysis.py annotations/<slug>.json`.

