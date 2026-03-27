from pathlib import Path


def is_text_based_pdf(file_path: Path) -> bool:
    """Return True if the PDF contains selectable text (not a scanned image)."""
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    return True
        return False
    except Exception:
        return False


def extract_text_pdfplumber(file_path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    try:
        import pdfplumber
        pages_text: list[str] = []
        with pdfplumber.open(str(file_path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages_text.append(text)
        return "\n".join(pages_text)
    except Exception as exc:
        raise RuntimeError(f"pdfplumber text extraction failed for '{file_path}': {exc}") from exc


def extract_tables_pdfplumber(file_path: Path, **kwargs) -> list[list[list[str]]]:
    """Extract all tables from all pages using pdfplumber.

    Returns a list of tables. Each table is a list of rows, each row is a list of cell strings.
    """
    try:
        import pdfplumber
        all_tables: list[list[list[str]]] = []
        with pdfplumber.open(str(file_path)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables(**kwargs)
                if tables:
                    for table in tables:
                        cleaned = [
                            [clean_cell(cell) for cell in row]
                            for row in table
                            if row
                        ]
                        if cleaned:
                            all_tables.append(cleaned)
        return all_tables
    except Exception as exc:
        raise RuntimeError(f"pdfplumber table extraction failed for '{file_path}': {exc}") from exc


def clean_cell(value) -> str:
    """Normalize a table cell: convert None to empty string, strip whitespace."""
    if value is None:
        return ""
    return str(value).strip()
