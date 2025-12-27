from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import fitz  # PyMuPDF
import re
import tempfile
import os
import requests

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
    output_type: str = Form("png")
):
    # Save uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        pdf_path = tmp.name

    doc = fitz.open(pdf_path)

    total_hits = 0
    first_match_data = None

    regex = re.compile(pattern)
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
    os.remove(pdf_path)

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
    
    return parse_first_match(first_match_data["text"])


def merge_rects(rects):
    x0 = min(r.x0 for r in rects)
    y0 = min(r.y0 for r in rects)
    x1 = max(r.x1 for r in rects)
    y1 = max(r.y1 for r in rects)
    return fitz.Rect(x0, y0, x1, y1)

# Custom parse function
def parse_first_match(match_text: str) -> dict:
    ## TODO: change prompt based on form year
    prompt = "## Output format: {year:amount}## ## Instruction: use the following information, apple's earning per share for 2022, 2023 and 2024, not diluted ## \n ## Information : \n" + match_text + "##"

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
