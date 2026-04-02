import PyPDF2
import io

def extract_text_from_pdf(file_stream) -> str:
    """
    Extracts text from a PDF file-like object.
    Supports both binary streams and file paths.
    """
    try:
        # If it's a path string, open it; if it's already a stream, use it.
        if isinstance(file_stream, str):
            with open(file_stream, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        else:
            # Assume it's a file-like object (e.g. FastAPI UploadFile.file)
            reader = PyPDF2.PdfReader(file_stream)
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text
    except Exception as e:
        print(f"[parser.py] Error extracting PDF text: {e}")
        return ""
