# weekday.py
from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

DAYS_TH = ["จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์"]

def parse_ddmmyyyy_th(s: str) -> tuple[date, str]:
    s = s.strip()
    try:
        d = datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="รูปแบบวันที่ไม่ถูกต้อง (ต้องเป็น DD/MM/YYYY)")
    calendar = "BE" if d.year >= 2400 else "CE"
    if calendar == "BE":
        y = d.year - 543
        try:
            d = d.replace(year=y)
        except ValueError:
            # กรณี 29 ก.พ. แล้วปีค.ศ.ที่แปลงไม่ leap (หาได้ยากมาก แต่กันไว้)
            d = d.replace(year=y, day=28)
    return d, calendar

@app.get("/api/weekday")
def get_weekday(date: str):
    """
    ตรวจสอบวันจริงจากวันที่
    date format: DD/MM/YYYY (พ.ศ. หรือ ค.ศ.)
    """
    d, cal = parse_ddmmyyyy_th(date)
    weekday = DAYS_TH[d.weekday()]
    # เพิ่มฟิลด์ debug เผื่อเช็คปัญหาที่ฝั่ง FE; ไม่บังคับใช้
    return JSONResponse(content={
        "date": date,
        "weekday": weekday,
        "resolved_gregorian": d.isoformat(),  # เช่น "2025-10-10"
        "calendar": cal                       # "BE" หรือ "CE"
    })
