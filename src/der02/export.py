"""Export helpers for der02: HTML, PDF.

The HTML export saves the rendered folium map to a string. The PDF
export is a minimal text-only PDF that embeds the HTML source. It is
NOT a rendered map — for a real rendered PDF, the user should open
the HTML in a browser and use print-to-PDF. This module exists so
the project ships with a `pdf_bytes()` API even without external
PDF libraries (weasyprint, imgkit, etc.) which would add dependencies.

A proper headless-browser rendering path (Playwright, Selenium) is a
reasonable follow-up if rendering fidelity becomes important.
"""

from __future__ import annotations


def html_to_pdf_bytes(html: str) -> bytes:
    """Encode `html` as a minimal PDF 1.4 file containing a text stream
    with the first 200 characters of the HTML.

    Parameters
    ----------
    html
        The HTML source string.

    Returns
    -------
    bytes
        A valid PDF (latin-1 encoded) with the HTML source as text.
    """
    # Escape parens and backslashes for the PDF text stream.
    escaped = html.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    body = f"BT /F1 8 Tf 50 750 Td ({escaped[:200]}) Tj ET"
    stream = f"<< /Length {len(body)} >>\nstream\n{body}\nendstream"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        stream,
        "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ]
    pdf = "%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n{obj}\nendobj\n"
    pdf += "xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n"
    pdf += "trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
    pdf += f"{len(pdf)}\n%%EOF"
    return pdf.encode("latin-1", errors="replace")


__all__ = ["html_to_pdf_bytes"]
