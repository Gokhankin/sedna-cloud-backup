import sys

pdf_path = "0101001_General Forecast Analysis (Only Reservation).pdf"

try:
    import pypdf
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    print("PYPDF EXTRACT:")
    print(text[:3000])
except Exception as e:
    print(f"pypdf failed: {e}")
    try:
        import subprocess
        out = subprocess.check_output(["pdftotext", pdf_path, "-"]).decode('utf-8', errors='replace')
        print("PDFTOTEXT EXTRACT:")
        print(out[:3000])
    except Exception as e2:
        print(f"pdftotext failed: {e2}")
