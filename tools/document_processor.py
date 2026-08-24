"""
Pillar 6: Universal Document & PDF Processor.
Safe lazy-loaded imports for pdfplumber, pypdf, docx, and pandas with automatic fallbacks.
"""

import os
import io
import json
import uuid
import time
import re
from typing import Dict, Any, List, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

try:
    import pandas as pd
except ImportError:
    pd = None

from config import DOCUMENTS_DIR

class UniversalDocumentProcessor:
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = upload_dir or DOCUMENTS_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def process_file(self, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """Parses any uploaded document format into structured text, tables, and metadata."""
        os.makedirs(self.upload_dir, exist_ok=True)
        
        clean_basename = re.sub(r'[^a-zA-Z0-9._-]', '_', os.path.basename(filename)) or "document.txt"
        file_id = f"doc_{uuid.uuid4().hex[:10]}"
        secure_filename = f"{file_id}_{clean_basename}"
        saved_path = os.path.join(self.upload_dir, secure_filename)
        
        try:
            with open(saved_path, "wb") as f:
                f.write(file_bytes)
        except Exception as write_err:
            print(f"[DocumentProcessor] Error writing to disk: {write_err}")

        ext = os.path.splitext(clean_basename)[1].lower()
        extracted_text = ""
        metadata = {
            "file_id": file_id,
            "filename": clean_basename,
            "secure_filename": secure_filename,
            "file_type": ext,
            "file_size_bytes": len(file_bytes),
            "created_at": time.time()
        }
        df_preview = None
        extracted_tables = []

        try:
            # 1. PDF Processor (pdfplumber + pypdf fallback)
            if ext == ".pdf":
                page_texts = []
                if pdfplumber is not None:
                    try:
                        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                            metadata["page_count"] = len(pdf.pages)
                            for i, page in enumerate(pdf.pages):
                                page_txt = page.extract_text(layout=True) or page.extract_text() or ""
                                tables = page.extract_tables()
                                if tables:
                                    for t in tables:
                                        t_clean = "\n".join([" | ".join([str(cell or "").strip() for cell in row]) for row in t if any(row)])
                                        extracted_tables.append(f"Table {len(extracted_tables)+1} (Page {i+1}):\n{t_clean}")
                                if page_txt.strip():
                                    page_texts.append(f"=== [Page {i+1}] ===\n{page_txt.strip()}")
                    except Exception:
                        pass

                if not page_texts and pypdf is not None:
                    try:
                        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                        metadata["page_count"] = len(reader.pages)
                        for i, page in enumerate(reader.pages):
                            txt = page.extract_text() or ""
                            if txt.strip():
                                page_texts.append(f"=== [Page {i+1}] ===\n{txt.strip()}")
                    except Exception:
                        pass

                if extracted_tables:
                    extracted_text = "\n\n".join(page_texts) + "\n\n=== EXTRACTED TABLES ===\n" + "\n\n".join(extracted_tables)
                else:
                    extracted_text = "\n\n".join(page_texts)

                if not extracted_text.strip():
                    extracted_text = f"[PDF '{clean_basename}' has {metadata.get('page_count', 0)} pages, but text was embedded as scanned images.]"

            # 2. Word Documents (.docx)
            elif ext == ".docx" and docx is not None:
                doc = docx.Document(io.BytesIO(file_bytes))
                paras = [p.text for p in doc.paragraphs if p.text.strip()]
                metadata["paragraph_count"] = len(paras)
                extracted_text = "\n\n".join(paras)

            # 3. CSV & Tabular Data
            elif ext in (".csv", ".tsv"):
                if pd is not None:
                    sep = "\t" if ext == ".tsv" else ","
                    df = pd.read_csv(io.BytesIO(file_bytes), sep=sep)
                    metadata["rows"] = len(df)
                    metadata["columns"] = list(df.columns)
                    df_preview = {
                        "shape": f"{df.shape[0]} rows × {df.shape[1]} columns",
                        "columns": list(df.columns),
                        "head": df.head(5).to_dict(orient="records")
                    }
                    extracted_text = f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns.\nColumns: {', '.join(df.columns)}\n\nFirst 10 Rows:\n" + df.head(10).to_string()
                else:
                    extracted_text = file_bytes.decode("utf-8", errors="ignore")

            # 4. Excel Spreadsheets (.xlsx, .xls)
            elif ext in (".xlsx", ".xls") and pd is not None:
                excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
                sheet_names = excel_file.sheet_names
                metadata["sheets"] = sheet_names
                sheets_text = []
                for sheet in sheet_names:
                    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet)
                    sheets_text.append(f"--- [Sheet: {sheet}] ({df.shape[0]} rows × {df.shape[1]} cols) ---\n" + df.head(10).to_string())
                extracted_text = "\n\n".join(sheets_text)

            # 5. Plain Text, Markdown, JSON
            else:
                extracted_text = file_bytes.decode("utf-8", errors="ignore")

        except Exception as e:
            extracted_text = f"[Error extracting text from {clean_basename}: {str(e)}]"

        words = extracted_text.split()
        metadata["word_count"] = len(words)
        metadata["preview"] = extracted_text[:400] + ("..." if len(extracted_text) > 400 else "")

        return {
            "file_id": file_id,
            "filename": clean_basename,
            "file_path": saved_path,
            "metadata": metadata,
            "content": extracted_text,
            "df_preview": df_preview
        }
