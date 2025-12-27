from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import fitz  # PyMuPDF
import re
import tempfile
import os
import requests
from bs4 import BeautifulSoup

def clean_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)

url = "https://apifreellm.com/api/chat"

headers = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
}


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html") as f:
        return f.read()


@app.post("/search")
async def search_pdf(
    file: UploadFile = File(...),
    pattern: str = Form(...),
    before: int = Form(20),
    after: int = Form(20),
    output_type: str = Form("png"),
    base: str = Form(""),
    cik: str = Form("")
):
    print("hi")
    regex = re.compile(pattern)
    suffix = Path(file.filename).suffix.lower()

    # Save uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        file_path = tmp.name
    if suffix == ".txt" or cik != "":
        if cik != "":
            text = get_company_10K(cik, 2024)
            print("Got company")
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            print("Text length before cleaning: ", len(text))
            text = clean_html(text)
            print("Text length after cleaning: ", len(text))
        context = "N/A"
        matches = list(regex.finditer(text))
        if matches:
            match = matches[0]
            start, end = match.span()

            context = text[max(0, start - before): min(len(text), end + after)]
        first_match_data = {
            "text": context,
        }
        if output_type == "text":
            return {
                "first_match": context,
                "total_hits": len(matches)
            }
    
        return parse_first_match(first_match_data["text"], base)

    doc = fitz.open(file_path)

    total_hits = 0
    first_match_data = None

    file_name = os.path.splitext(file.filename)[0]

    for page_number, page in enumerate(doc):
        text = page.get_text()
        matches = list(regex.finditer(text))
        total_hits += len(matches)

        if matches and first_match_data is None:
            match = matches[0]
            start, end = match.span()

            context = text[max(0, start - before): min(len(text), end + after)]

            # Find rectangles for highlight
            text_instances = page.search_for(match.group())
            context_instances = page.search_for(context)

            if context_instances:
                merged_rect = merge_rects(context_instances)
                page.draw_rect(merged_rect, color=(1, 0, 0), width=2)

            if text_instances:
                rect = text_instances[0]
                page.draw_rect(rect, color=(1, 0, 0), width=2)

                # Save highlighted page as image
                pix = page.get_pixmap(dpi=150)
                image_path = f"static/{file_name}.png"
                pix.save(image_path)

            first_match_data = {
                "page": page_number + 1,
                "text": context,
            }

    doc.close()
    os.remove(file_path)

    if not first_match_data:
        return JSONResponse({"message": "No matches found"})

    if output_type == "png":
        return RedirectResponse(
        url=f"/static/{file_name}.png",
        status_code=302
    )
    elif output_type == "text":
        return {
            "first_match": first_match_data,
            "total_hits": total_hits
        }
    
    return parse_first_match(first_match_data["text"], base)


def merge_rects(rects):
    x0 = min(r.x0 for r in rects)
    y0 = min(r.y0 for r in rects)
    x1 = max(r.x1 for r in rects)
    y1 = max(r.y1 for r in rects)
    return fitz.Rect(x0, y0, x1, y1)

# Custom parse function
def parse_first_match(match_text: str, base: str) -> dict:
    print("Base is: ",base)
    if base == "" :
        base = "## Output format: {year:amount}, do not include any explaining text## ## Instruction: use the following information, apple's earning per share for the last 3 years, basic and not diluted ## \n ## Information : \n" 
    prompt = base + match_text + "##"

    data = {
        "message": prompt
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        # Check the API “status” field
        if result.get("status") == "success":
            print("AI Response:", result["response"])
        else:
            print("API Error:", result.get("error"))

    except Exception as e:
        print("Request failed:", str(e))
    return {
        "original_text": match_text,
        "response": result["response"],
        "length": len(prompt)
    }

def get_company_10K(cik: str, year: int):
    headers = {
    "User-Agent": "agent@gmail.com"
}

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    filings = data["filings"]["recent"]
    for i, form in enumerate(filings["form"]):
        if form == "10-K" and filings["filingDate"][i].startswith("2024"):
            accession = filings["accessionNumber"][i].replace("-", "")
            primary_doc = filings["primaryDocument"][i]
            print(accession, primary_doc)
    accession = accession  # from previous step
    doc = primary_doc

    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}"

    ten_k = requests.get(doc_url, headers=headers).text
    soup = BeautifulSoup(ten_k, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text