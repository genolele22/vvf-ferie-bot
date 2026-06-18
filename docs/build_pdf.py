#!/usr/bin/env python3
"""
Converte le guide Markdown in PDF stampabili.
Uso:  /home/genolele22/.cache/pdfvenv/bin/python build_pdf.py
Genera guida-vigile.pdf e guida-furiere.pdf nella stessa cartella.
"""
import os
from pathlib import Path

QUI = Path(__file__).resolve().parent

# Forza l'emoji monocromatico (Noto Emoji) al posto di quello a colori: i PDF
# pesano ~4x meno e si stampano meglio in bianco e nero. Va impostato PRIMA di
# importare weasyprint (fontconfig si inizializza all'import).
_FC = QUI / ".fonts-no-color-emoji.conf"
_FC.write_text("""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <include ignore_missing="no">/etc/fonts/fonts.conf</include>
  <selectfont><rejectfont><pattern>
    <patelt name="family"><string>Noto Color Emoji</string></patelt>
  </pattern></rejectfont></selectfont>
</fontconfig>
""", encoding="utf-8")
os.environ.setdefault("FONTCONFIG_FILE", str(_FC))

import markdown
from weasyprint import HTML

GUIDE = [
    ("guida-vigile.md",  "guida-vigile.pdf",  "Guida per il vigile"),
    ("guida-furiere.md", "guida-furiere.pdf", "Guida per il furiere"),
]

CSS = """
@page {
    size: A4;
    margin: 1.8cm 1.6cm 2cm 1.6cm;
    @bottom-center {
        content: "VVF Genova — Turno B   ·   pag. " counter(page) " di " counter(pages);
        font-family: 'Noto Sans', sans-serif;
        font-size: 8pt;
        color: #999;
    }
}
* { box-sizing: border-box; }
body {
    font-family: 'Noto Sans', 'Noto Emoji', 'Noto Sans Symbols2', Verdana, sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #1a1a1a;
}
h1 {
    color: #b8231e;
    font-size: 20pt;
    border-bottom: 3px solid #b8231e;
    padding-bottom: 6px;
    margin: 0 0 14px 0;
}
h1:not(:first-of-type) { page-break-before: always; }
h2 {
    color: #b8231e;
    font-size: 14pt;
    margin-top: 22px;
    border-left: 4px solid #b8231e;
    padding-left: 8px;
}
h3 { font-size: 11.5pt; margin-top: 16px; color: #333; }
p { margin: 6px 0; }
ul, ol { margin: 6px 0 10px 0; padding-left: 22px; }
li { margin: 3px 0; }
strong { color: #000; }
code {
    background: #f2f2f2;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 1px 5px;
    font-family: 'Noto Mono', monospace;
    font-size: 9.5pt;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    font-size: 9.8pt;
}
th, td {
    border: 1px solid #ccc;
    padding: 6px 9px;
    text-align: left;
    vertical-align: top;
}
th { background: #b8231e; color: #fff; font-weight: 600; }
tr:nth-child(even) td { background: #faf6f6; }
blockquote {
    background: #fff7e6;
    border-left: 4px solid #e0a800;
    margin: 12px 0;
    padding: 8px 14px;
    border-radius: 0 4px 4px 0;
}
blockquote p { margin: 4px 0; }
hr { border: none; border-top: 1px solid #ddd; margin: 18px 0; }
"""

def main():
    for md_name, pdf_name, titolo in GUIDE:
        md_path = QUI / md_name
        if not md_path.exists():
            print(f"SALTO {md_name}: non trovato")
            continue
        testo = md_path.read_text(encoding="utf-8")
        body = markdown.markdown(
            testo,
            extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        )
        html = f"""<!DOCTYPE html><html lang="it"><head><meta charset="utf-8">
<title>{titolo}</title><style>{CSS}</style></head><body>{body}</body></html>"""
        out = QUI / pdf_name
        HTML(string=html, base_url=str(QUI)).write_pdf(str(out))
        print(f"OK  {pdf_name}  ({out.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()
