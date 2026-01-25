from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from Levenshtein import distance
# import fitz  # PyMuPDF
import re
import tempfile
import os
import requests
from bs4 import BeautifulSoup
from typing import Optional
from groq import Groq
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from mangum import Mangum


load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

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
handler = Mangum(app)
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
companies_list = {'3M': 'MMM', 'A. O. Smith': 'AOS', 'Abbott Laboratories': 'ABT', 'AbbVie': 'ABBV', 'Accenture': 'ACN', 'Adobe Inc.': 'ADBE', 'Advanced Micro Devices': 'AMD', 'AES Corporation': 'AES', 'Aflac': 'AFL', 'Agilent Technologies': 'A', 'Air Products': 'APD', 'Airbnb': 'ABNB', 'Akamai Technologies': 'AKAM', 'Albemarle Corporation': 'ALB', 'Alexandria Real Estate Equities': 'ARE', 'Align Technology': 'ALGN', 'Allegion': 'ALLE', 'Alliant Energy': 'LNT', 'Allstate': 'ALL', 'Alphabet Inc. (Class A)': 'GOOGL', 'Alphabet Inc. (Class C)': 'GOOG', 'Altria': 'MO', 'Amazon': 'AMZN', 'Amcor': 'AMCR', 'Ameren': 'AEE', 'American Electric Power': 'AEP', 'American Express': 'AXP', 'American International Group': 'AIG', 'American Tower': 'AMT', 'American Water Works': 'AWK', 'Ameriprise Financial': 'AMP', 'Ametek': 'AME', 'Amgen': 'AMGN', 'Amphenol': 'APH', 'Analog Devices': 'ADI', 'Ansys': 'ANSS', 'Aon plc': 'AON', 'APA Corporation': 'APA', 'Apollo Global Management': 'APO', 'Apple Inc.': 'AAPL', 'Applied Materials': 'AMAT', 'Aptiv': 'APTV', 'Arch Capital Group': 'ACGL', 'Archer Daniels Midland': 'ADM', 'Arista Networks': 'ANET', 'Arthur J. Gallagher & Co.': 'AJG', 'Assurant': 'AIZ', 'AT&T': 'T', 'Atmos Energy': 'ATO', 'Autodesk': 'ADSK', 'Automatic Data Processing': 'ADP', 'AutoZone': 'AZO', 'AvalonBay Communities': 'AVB', 'Avery Dennison': 'AVY', 'Axon Enterprise': 'AXON', 'Baker Hughes': 'BKR', 'Ball Corporation': 'BALL', 'Bank of America': 'BAC', 'Baxter International': 'BAX', 'Becton Dickinson': 'BDX', 'Berkshire Hathaway': 'BRK.B', 'Best Buy': 'BBY', 'Bio-Techne': 'TECH', 'Biogen': 'BIIB', 'BlackRock': 'BLK', 'Blackstone Inc.': 'BX', 'BNY Mellon': 'BK', 'Boeing': 'BA', 'Booking Holdings': 'BKNG', 'Boston Scientific': 'BSX', 'Bristol Myers Squibb': 'BMY', 'Broadcom': 'AVGO', 'Broadridge Financial Solutions': 'BR', 'Brown & Brown': 'BRO', 'Brown–Forman': 'BF.B', 'Builders FirstSource': 'BLDR', 'Bunge Global': 'BG', 'BXP, Inc.': 'BXP', 'C.H. Robinson': 'CHRW', 'Cadence Design Systems': 'CDNS', 'Caesars Entertainment': 'CZR', 'Camden Property Trust': 'CPT', "Campbell's Company (The)": 'CPB', 'Capital One': 'COF', 'Cardinal Health': 'CAH', 'CarMax': 'KMX', 'Carnival': 'CCL', 'Carrier Global': 'CARR', 'Caterpillar Inc.': 'CAT', 'Cboe Global Markets': 'CBOE', 'CBRE Group': 'CBRE', 'CDW Corporation': 'CDW', 'Cencora': 'COR', 'Centene Corporation': 'CNC', 'CenterPoint Energy': 'CNP', 'CF Industries': 'CF', 'Charles River Laboratories': 'CRL', 'Charles Schwab Corporation': 'SCHW', 'Charter Communications': 'CHTR', 'Chevron Corporation': 'CVX', 'Chipotle Mexican Grill': 'CMG', 'Chubb Limited': 'CB', 'Church & Dwight': 'CHD', 'Cigna': 'CI', 'Cincinnati Financial': 'CINF', 'Cintas': 'CTAS', 'Cisco': 'CSCO', 'Citigroup': 'C', 'Citizens Financial Group': 'CFG', 'Clorox': 'CLX', 'CME Group': 'CME', 'CMS Energy': 'CMS', 'Coca-Cola Company (The)': 'KO', 'Cognizant': 'CTSH', 'Coinbase': 'COIN', 'Colgate-Palmolive': 'CL', 'Comcast': 'CMCSA', 'Conagra Brands': 'CAG', 'ConocoPhillips': 'COP', 'Consolidated Edison': 'ED', 'Constellation Brands': 'STZ', 'Constellation Energy': 'CEG', 'Cooper Companies (The)': 'COO', 'Copart': 'CPRT', 'Corning Inc.': 'GLW', 'Corpay': 'CPAY', 'Corteva': 'CTVA', 'CoStar Group': 'CSGP', 'Costco': 'COST', 'Coterra': 'CTRA', 'CrowdStrike': 'CRWD', 'Crown Castle': 'CCI', 'CSX Corporation': 'CSX', 'Cummins': 'CMI', 'CVS Health': 'CVS', 'Danaher Corporation': 'DHR', 'Darden Restaurants': 'DRI', 'DaVita': 'DVA', 'Dayforce': 'DAY', 'Deckers Brands': 'DECK', 'Deere & Company': 'DE', 'Dell Technologies': 'DELL', 'Delta Air Lines': 'DAL', 'Devon Energy': 'DVN', 'Dexcom': 'DXCM', 'Diamondback Energy': 'FANG', 'Digital Realty': 'DLR', 'Dollar General': 'DG', 'Dollar Tree': 'DLTR', 'Dominion Energy': 'D', "Domino's": 'DPZ', 'DoorDash': 'DASH', 'Dover Corporation': 'DOV', 'Dow Inc.': 'DOW', 'D. R. Horton': 'DHI', 'DTE Energy': 'DTE', 'Duke Energy': 'DUK', 'DuPont': 'DD', 'Eastman Chemical Company': 'EMN', 'Eaton Corporation': 'ETN', 'eBay Inc.': 'EBAY', 'Ecolab': 'ECL', 'Edison International': 'EIX', 'Edwards Lifesciences': 'EW', 'Electronic Arts': 'EA', 'Elevance Health': 'ELV', 'Emerson Electric': 'EMR', 'Enphase Energy': 'ENPH', 'Entergy': 'ETR', 'EOG Resources': 'EOG', 'EPAM Systems': 'EPAM', 'EQT Corporation': 'EQT', 'Equifax': 'EFX', 'Equinix': 'EQIX', 'Equity Residential': 'EQR', 'Erie Indemnity': 'ERIE', 'Essex Property Trust': 'ESS', 'Estée Lauder Companies (The)': 'EL', 'Everest Group': 'EG', 'Evergy': 'EVRG', 'Eversource Energy': 'ES', 'Exelon': 'EXC', 'Expand Energy': 'EXE', 'Expedia Group': 'EXPE', 'Expeditors International': 'EXPD', 'Extra Space Storage': 'EXR', 'ExxonMobil': 'XOM', 'F5, Inc.': 'FFIV', 'FactSet': 'FDS', 'Fair Isaac': 'FICO', 'Fastenal': 'FAST', 'Federal Realty Investment Trust': 'FRT', 'FedEx': 'FDX', 'Fidelity National Information Services': 'FIS', 'Fifth Third Bancorp': 'FITB', 'First Solar': 'FSLR', 'FirstEnergy': 'FE', 'Fiserv': 'FI', 'Ford Motor Company': 'F', 'Fortinet': 'FTNT', 'Fortive': 'FTV', 'Fox Corporation (Class A)': 'FOXA', 'Fox Corporation (Class B)': 'FOX', 'Franklin Resources': 'BEN', 'Freeport-McMoRan': 'FCX', 'Garmin': 'GRMN', 'Gartner': 'IT', 'GE Aerospace': 'GE', 'GE HealthCare': 'GEHC', 'GE Vernova': 'GEV', 'Gen Digital': 'GEN', 'Generac': 'GNRC', 'General Dynamics': 'GD', 'General Mills': 'GIS', 'General Motors': 'GM', 'Genuine Parts Company': 'GPC', 'Gilead Sciences': 'GILD', 'Global Payments': 'GPN', 'Globe Life': 'GL', 'GoDaddy': 'GDDY', 'Goldman Sachs': 'GS', 'Halliburton': 'HAL', 'Hartford (The)': 'HIG', 'Hasbro': 'HAS', 'HCA Healthcare': 'HCA', 'Healthpeak Properties': 'DOC', 'Henry Schein': 'HSIC', 'Hershey Company (The)': 'HSY', 'Hess Corporation': 'HES', 'Hewlett Packard Enterprise': 'HPE', 'Hilton Worldwide': 'HLT', 'Hologic': 'HOLX', 'Home Depot (The)': 'HD', 'Honeywell': 'HON', 'Hormel Foods': 'HRL', 'Host Hotels & Resorts': 'HST', 'Howmet Aerospace': 'HWM', 'HP Inc.': 'HPQ', 'Hubbell Incorporated': 'HUBB', 'Humana': 'HUM', 'Huntington Bancshares': 'HBAN', 'Huntington Ingalls Industries': 'HII', 'IBM': 'IBM', 'IDEX Corporation': 'IEX', 'Idexx Laboratories': 'IDXX', 'Illinois Tool Works': 'ITW', 'Incyte': 'INCY', 'Ingersoll Rand': 'IR', 'Insulet Corporation': 'PODD', 'Intel': 'INTC', 'Intercontinental Exchange': 'ICE', 'International Flavors & Fragrances': 'IFF', 'International Paper': 'IP', 'Interpublic Group of Companies (The)': 'IPG', 'Intuit': 'INTU', 'Intuitive Surgical': 'ISRG', 'Invesco': 'IVZ', 'Invitation Homes': 'INVH', 'IQVIA': 'IQV', 'Iron Mountain': 'IRM', 'J.B. Hunt': 'JBHT', 'Jabil': 'JBL', 'Jack Henry & Associates': 'JKHY', 'Jacobs Solutions': 'J', 'Johnson & Johnson': 'JNJ', 'Johnson Controls': 'JCI', 'JPMorgan Chase': 'JPM', 'Juniper Networks': 'JNPR', 'Kellanova': 'K', 'Kenvue': 'KVUE', 'Keurig Dr Pepper': 'KDP', 'KeyCorp': 'KEY', 'Keysight Technologies': 'KEYS', 'Kimberly-Clark': 'KMB', 'Kimco Realty': 'KIM', 'Kinder Morgan': 'KMI', 'KKR & Co.': 'KKR', 'KLA Corporation': 'KLAC', 'Kraft Heinz': 'KHC', 'Kroger': 'KR', 'L3Harris': 'LHX', 'Labcorp': 'LH', 'Lam Research': 'LRCX', 'Lamb Weston': 'LW', 'Las Vegas Sands': 'LVS', 'Leidos': 'LDOS', 'Lennar': 'LEN', 'Lennox International': 'LII', 'Lilly (Eli)': 'LLY', 'Linde plc': 'LIN', 'Live Nation Entertainment': 'LYV', 'LKQ Corporation': 'LKQ', 'Lockheed Martin': 'LMT', 'Loews Corporation': 'L', "Lowe's": 'LOW', 'Lululemon Athletica': 'LULU', 'LyondellBasell': 'LYB', 'M&T Bank': 'MTB', 'Marathon Petroleum': 'MPC', 'MarketAxess': 'MKTX', 'Marriott International': 'MAR', 'Marsh McLennan': 'MMC', 'Martin Marietta Materials': 'MLM', 'Masco': 'MAS', 'Mastercard': 'MA', 'Match Group': 'MTCH', 'McCormick & Company': 'MKC', "McDonald's": 'MCD', 'McKesson Corporation': 'MCK', 'Medtronic': 'MDT', 'Merck & Co.': 'MRK', 'Meta Platforms': 'META', 'MetLife': 'MET', 'Mettler Toledo': 'MTD', 'MGM Resorts': 'MGM', 'Microchip Technology': 'MCHP', 'Micron Technology': 'MU', 'Microsoft': 'MSFT', 'Mid-America Apartment Communities': 'MAA', 'Moderna': 'MRNA', 'Mohawk Industries': 'MHK', 'Molina Healthcare': 'MOH', 'Molson Coors Beverage Company': 'TAP', 'Mondelez International': 'MDLZ', 'Monolithic Power Systems': 'MPWR', 'Monster Beverage': 'MNST', "Moody's Corporation": 'MCO', 'Morgan Stanley': 'MS', 'Mosaic Company (The)': 'MOS', 'Motorola Solutions': 'MSI', 'MSCI Inc.': 'MSCI', 'Nasdaq, Inc.': 'NDAQ', 'NetApp': 'NTAP', 'Netflix': 'NFLX', 'Newmont': 'NEM', 'News Corp (Class A)': 'NWSA', 'News Corp (Class B)': 'NWS', 'NextEra Energy': 'NEE', 'Nike, Inc.': 'NKE', 'NiSource': 'NI', 'Nordson Corporation': 'NDSN', 'Norfolk Southern': 'NSC', 'Northern Trust': 'NTRS', 'Northrop Grumman': 'NOC', 'Norwegian Cruise Line Holdings': 'NCLH', 'NRG Energy': 'NRG', 'Nucor': 'NUE', 'Nvidia': 'NVDA', 'NVR, Inc.': 'NVR', 'NXP Semiconductors': 'NXPI', 'O’Reilly Automotive': 'ORLY', 'Occidental Petroleum': 'OXY', 'Old Dominion': 'ODFL', 'Omnicom Group': 'OMC', 'ON Semiconductor': 'ON', 'Oneok': 'OKE', 'Oracle Corporation': 'ORCL', 'Otis Worldwide': 'OTIS', 'Paccar': 'PCAR', 'Packaging Corporation of America': 'PKG', 'Palantir Technologies': 'PLTR', 'Palo Alto Networks': 'PANW', 'Paramount Global': 'PARA', 'Parker Hannifin': 'PH', 'Paychex': 'PAYX', 'Paycom': 'PAYC', 'PayPal': 'PYPL', 'Pentair': 'PNR', 'PepsiCo': 'PEP', 'Pfizer': 'PFE', 'PG&E Corporation': 'PCG', 'Philip Morris International': 'PM', 'Phillips 66': 'PSX', 'Pinnacle West Capital': 'PNW', 'PNC Financial Services': 'PNC', 'Pool Corporation': 'POOL', 'PPG Industries': 'PPG', 'PPL Corporation': 'PPL', 'Principal Financial Group': 'PFG', 'Procter & Gamble': 'PG', 'Progressive Corporation': 'PGR', 'Prologis': 'PLD', 'Prudential Financial': 'PRU', 'Public Service Enterprise Group': 'PEG', 'PTC Inc.': 'PTC', 'Public Storage': 'PSA', 'PulteGroup': 'PHM', 'Quanta Services': 'PWR', 'Qualcomm': 'QCOM', 'Quest Diagnostics': 'DGX', 'Ralph Lauren Corporation': 'RL', 'Raymond James Financial': 'RJF', 'RTX Corporation': 'RTX', 'Realty Income': 'O', 'Regency Centers': 'REG', 'Regeneron Pharmaceuticals': 'REGN', 'Regions Financial Corporation': 'RF', 'Republic Services': 'RSG', 'ResMed': 'RMD', 'Revvity': 'RVTY', 'Rockwell Automation': 'ROK', 'Rollins, Inc.': 'ROL', 'Roper Technologies': 'ROP', 'Ross Stores': 'ROST', 'Royal Caribbean Group': 'RCL', 'S&P Global': 'SPGI', 'Salesforce': 'CRM', 'SBA Communications': 'SBAC', 'Schlumberger': 'SLB', 'Seagate Technology': 'STX', 'Sempra': 'SRE', 'ServiceNow': 'NOW', 'Sherwin-Williams': 'SHW', 'Simon Property Group': 'SPG', 'Skyworks Solutions': 'SWKS', 'J.M. Smucker Company (The)': 'SJM', 'Smurfit Westrock': 'SW', 'Snap-on': 'SNA', 'Solventum': 'SOLV', 'Southern Company': 'SO', 'Southwest Airlines': 'LUV', 'Stanley Black & Decker': 'SWK', 'Starbucks': 'SBUX', 'State Street Corporation': 'STT', 'Steel Dynamics': 'STLD', 'Steris': 'STE', 'Stryker Corporation': 'SYK', 'Supermicro': 'SMCI', 'Synchrony Financial': 'SYF', 'Synopsys': 'SNPS', 'Sysco': 'SYY', 'T-Mobile US': 'TMUS', 'T. Rowe Price': 'TROW', 'Take-Two Interactive': 'TTWO', 'Tapestry, Inc.': 'TPR', 'Targa Resources': 'TRGP', 'Target Corporation': 'TGT', 'TE Connectivity': 'TEL', 'Teledyne Technologies': 'TDY', 'Teradyne': 'TER', 'Tesla, Inc.': 'TSLA', 'Texas Instruments': 'TXN', 'Texas Pacific Land Corporation': 'TPL', 'Textron': 'TXT', 'Thermo Fisher Scientific': 'TMO', 'TJX Companies': 'TJX', 'TKO Group Holdings': 'TKO', 'Tractor Supply': 'TSCO', 'Trane Technologies': 'TT', 'TransDigm Group': 'TDG', 'Travelers Companies (The)': 'TRV', 'Trimble Inc.': 'TRMB', 'Truist Financial': 'TFC', 'Tyler Technologies': 'TYL', 'Tyson Foods': 'TSN', 'U.S. Bancorp': 'USB', 'Uber': 'UBER', 'UDR, Inc.': 'UDR', 'Ulta Beauty': 'ULTA', 'Union Pacific Corporation': 'UNP', 'United Airlines Holdings': 'UAL', 'United Parcel Service': 'UPS', 'United Rentals': 'URI', 'UnitedHealth Group': 'UNH', 'Universal Health Services': 'UHS', 'Valero Energy': 'VLO', 'Ventas': 'VTR', 'Veralto': 'VLTO', 'Verisign': 'VRSN', 'Verisk Analytics': 'VRSK', 'Verizon': 'VZ', 'Vertex Pharmaceuticals': 'VRTX', 'Viatris': 'VTRS', 'Vici Properties': 'VICI', 'Visa Inc.': 'V', 'Vistra Corp.': 'VST', 'Vulcan Materials Company': 'VMC', 'W. R. Berkley Corporation': 'WRB', 'W. W. Grainger': 'GWW', 'Wabtec': 'WAB', 'Walgreens Boots Alliance': 'WBA', 'Walmart': 'WMT', 'Walt Disney Company (The)': 'DIS', 'Warner Bros. Discovery': 'WBD', 'Waste Management': 'WM', 'Waters Corporation': 'WAT', 'WEC Energy Group': 'WEC', 'Wells Fargo': 'WFC', 'Welltower': 'WELL', 'West Pharmaceutical Services': 'WST', 'Western Digital': 'WDC', 'Weyerhaeuser': 'WY', 'Williams-Sonoma, Inc.': 'WSM', 'Williams Companies': 'WMB', 'Willis Towers Watson': 'WTW', 'Workday, Inc.': 'WDAY', 'Wynn Resorts': 'WYNN', 'Xcel Energy': 'XEL', 'Xylem Inc.': 'XYL', 'Yum! Brands': 'YUM', 'Zebra Technologies': 'ZBRA', 'Zimmer Biomet': 'ZBH', 'Zoetis': 'ZTS'}

companies = list(companies_list.keys())

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,   # REQUIRED
            "companies": companies
        }
    )

@app.post("/search")
async def search_pdf(
    file: Optional[UploadFile] = File(None),
    pattern: str = Form(...),
    before: int = Form(1800),
    after: int = Form(800),
    output_type: str = Form("text"),
    base: str = Form(""),
    cik: str = Form(""), ## AAPL CIK 0000320193
    year: int = Form(2025),
    company: str = Form(""),
    model: str = Form("text")
):
    # regex = re.compile(pattern, re.IGNORECASE)
    regex = re.compile(pattern)
    suffix = Path(file.filename).suffix.lower()
    if (file is not None):
        # Save uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            file_path = tmp.name
    if company != "":
        cik = str(get_company_cik(company))
        cik = (10 - len(cik))*"0" + cik
    if suffix == ".txt" or cik != "":
        if cik != "":
            text = get_company_10K(cik, year)
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

            context = text[max(0, start - before): min(len(text)-1, end + after)]
        first_match_data = {
            "text": context,
        }
        if output_type == "parse":
            # return parse_first_match(first_match_data["text"], base)
            return parse_groq(first_match_data["text"], base, model)
        return {
            "first_match": context,
            "total_hits": len(matches)
        }
    

    # doc = fitz.open(file_path)

    # total_hits = 0
    # first_match_data = None

    # file_name = os.path.splitext(file.filename)[0]

    # for page_number, page in enumerate(doc):
    #     text = page.get_text()
    #     matches = list(regex.finditer(text))
    #     total_hits += len(matches)

    #     if matches and first_match_data is None:
    #         match = matches[0]
    #         start, end = match.span()
    #         print("len text:",len(text))
    #         print("end + after:",end+after)
    #         context = text[max(0, start - before): min(len(text)-1, end + after)]

    #         # Find rectangles for highlight
    #         text_instances = page.search_for(match.group())
    #         context_instances = page.search_for(context)
    #         print("context:",context_instances)
    #         if context_instances:
    #             merged_rect = merge_rects(context_instances)
    #             print("merged_rect:",merged_rect)
    #             page.draw_rect(merged_rect, color=(1, 0, 0), width=2)

    #         if text_instances:
    #             rect = text_instances[0]
    #             page.draw_rect(rect, color=(1, 0, 0), width=2)

    #             # Save highlighted page as image
    #             pix = page.get_pixmap(dpi=150)
    #             image_path = f"static/{file_name}.png"
    #             pix.save(image_path)

    #         first_match_data = {
    #             "page": page_number + 1,
    #             "text": context,
    #         }

    # doc.close()
    # os.remove(file_path)

    # if not first_match_data:
    #     return JSONResponse({"message": "No matches found"})

    # if output_type == "png":
    #     return RedirectResponse(
    #     url=f"/static/{file_name}.png",
    #     status_code=302
    # )
    # elif output_type == "text":
    #     return {
    #         "first_match": first_match_data,
    #         "total_hits": total_hits
    #     }
    
    # # return parse_first_match(first_match_data["text"], base)
    # return parse_groq(first_match_data["text"], base, model)


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

def parse_groq(match_text: str, base: str, model = "openai/gpt-oss-120b") -> dict:
    print("Base is: ",base)
    if base == "" :
        base = "## Output format: [year,amount], do not include any explaining text## ## Instruction: find the last reported earnings per share not diluted (or net income per share not diluted), make sure it is basic and not diluted ## \n ## Context : \n" 
    prompt = base + match_text + "##"

    data = {
        "message": prompt
    }

    try:
        completion = req_groq(prompt, model)
        print(completion)
        result = {
            'status': "success" if completion.choices[0].finish_reason == 'stop' else "failed",
            'error': completion,
            'response': completion.choices[0].message.content
            }

    except Exception as e:
        print("Request failed:", str(e))
    return {
        "original_text": match_text,
        "response": result["response"],
        "length": len(prompt)
    }

def req_groq(prompt, model="openai/gpt-oss-120b"):
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        # model="groq/compound",
        # model = "meta-llama/llama-4-scout-17b-16e-instruct",##meta-llama/llama-4-maverick-17b-128e-instruct
        # model = "qwen/qwen3-32b",
        model = model, ## 20b is less powerful openai/gpt-oss-120b
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )
    return completion

def get_company_10K(cik: str, year: int):
    headers = {
    "User-Agent": "agent@gmail.com"
}

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    filings = data["filings"]["recent"]
    print(f"Year is {year}")
    for i, form in enumerate(filings["form"]):
        if form == "10-K" and filings["filingDate"][i].startswith(str(year)):
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


def get_company_cik(company:str):
    df = pd.read_csv("./data/constituents.csv", index_col=None)
    df = df[["Symbol", "Security", "CIK"]]
    if company in df["Symbol"].values:
        row = df.loc[df["Symbol"] == company].iloc[0]
        print("CIK recovered from symbol: ", row["CIK"])
        return row["CIK"]
    
    if company in df["Security"].values:
        row = df.loc[df["Security"] == company].iloc[0]
        print("CIK recovered from security: ", row["CIK"])
        return row["CIK"]
    
    matches = df[df['Security'].str.contains(company.lower(), case=False, na=False)]
    if (len(matches)):
        row = matches.iloc[0]
        print("CIK recovered from security (name substr): ", row["CIK"])
        return row["CIK"]

    df["lev_distance"] = df["Security"].apply(lambda x: distance(x.lower(), company.lower()))

    # Get the row with the smallest distance
    closest_row = df.loc[df["lev_distance"].idxmin()]
    if (len(closest_row)):
        print(f"CIK recovered from closest company {closest_row['Security']} with distance {closest_row['lev_distance']}: {closest_row['CIK']}")
        return closest_row["CIK"]
    print("Couldn't find CIK")
    return ""
    

@app.get("/parse")    
def parse_text(
    year: int,
    cik: str = "", ## AAPL CIK 0000320193
    company: str = "",
    base: str = "",
    model: str = "openai/gpt-oss-120b",
    pattern: str = "(?:Basic earnings|Basic net income|Earnings|Net income) per (?:common )?share",
    before: int = 2000,
    after: int = 800
):
    # regex = re.compile(pattern, re.IGNORECASE)
    regex = re.compile(pattern)
    if company != "":
        cik = str(get_company_cik(company))
        cik = (10 - len(cik))*"0" + cik
    if cik != "":
        text = get_company_10K(cik, year)
        print("Got company")
    print("Text length before cleaning: ", len(text))
    text = clean_html(text)
    print("Text length after cleaning: ", len(text))
    context = "N/A"
    matches = list(regex.finditer(text))
    if matches:
        match = matches[0]
        start, end = match.span()

        context = text[max(0, start - before): min(len(text)-1, end + after)]
    first_match_data = {
        "text": context,
    }
    return parse_groq(first_match_data["text"], base, model)