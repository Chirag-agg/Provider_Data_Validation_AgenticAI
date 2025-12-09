import os
import fitz  # PyMuPDF
from crewai.tools import BaseTool
from pydantic import Field


class ExtractTextFromPDFTool(BaseTool):
    """Tool to safely extract text from PDFs using PyMuPDF."""

    # Pydantic field definitions (REQUIRED in new CrewAI)
    name: str = Field(default="extract_text_from_pdf", description="Tool name")
    description: str = Field(
        default=(
            "Extracts all text from a PDF file. "
            "Use ONLY when a valid pdf_path is explicitly provided. "
            "Do NOT guess or hallucinate file paths."
        )
    )

    # Actual execution method
    def _run(self, pdf_path: str = None) -> str:
        if not pdf_path:
            return (
                "ERROR: No pdf_path provided. "
                "You must supply a real existing file path. "
                "Never call this tool without a valid path."
            )

        if not os.path.isfile(pdf_path):
            return (
                f"ERROR: File does not exist: {pdf_path}. "
                "Tool ignored. Provide a real file path."
            )

        try:
            doc = fitz.open(pdf_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text.strip()

        except Exception as e:
            return f"ERROR: Could not read PDF '{pdf_path}'. Details: {str(e)}"
