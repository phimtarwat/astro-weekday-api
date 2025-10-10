from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import zoneinfo
from typing import Optional

app = FastAPI()

DAYS_TH = ["จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์"]

# ------------------------------
# ฟังก์ชันเดิม: แปลงวันที่ พ.ศ./ค.ศ.
# ------------------------------
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
            # กรณี 29 ก.พ. แล้วปีค.ศ.ที่แปลงไม่ leap (กันไว้)
            d = d.replace(year=y, day=28)
    return d, calendar

# ------------------------------
# Endpoint เดิม (ยังใช้ได้เหมือนเดิม)
# ------------------------------
@app.get("/api/weekday")
def get_weekday(date: str):
    """
    ตรวจสอบวันจริงจากวันที่ (DD/MM/YYYY)
    """
    d, cal = parse_ddmmyyyy_th(date)
    weekday = DAYS_TH[d.weekday()]
    return JSONResponse(content={
        "date": date,
        "weekday": weekday,
        "resolved_gregorian": d.isoformat(),
        "calendar": cal
    })


# ------------------------------
# 🪐 Endpoint ใหม่: สำหรับโหราศาสตร์
# ------------------------------
@app.get("/api/astro-weekday")
def get_astro_weekday(
    date: str,
    time: Optional[str] = None,
    timezone: Optional[str] = "Asia/Bangkok",
    place: Optional[str] = None
):
    """
    ตรวจสอบวันจริง + เวลา + timezone + สถานที่เกิด (เพื่อใช้ในโหราศาสตร์)
    ตัวอย่าง:
      /api/astro-weekday?date=24/11/2514&time=11:00&timezone=Asia/Bangkok&place=Bangkok
    """
    # แปลงวันที่
    d, cal = parse_ddmmyyyy_th(date)

    # แปลงเวลา
    if time:
        try:
            t = datetime.strptime(time, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="รูปแบบเวลาไม่ถูกต้อง (ต้องเป็น HH:MM)")
    else:
        t = datetime.min.time()

    # รวมวัน+เวลา
    dt_local = datetime.combine(d, t)

    # ใช้ timezone (IANA เช่น Asia/Tokyo, Europe/London)
    try:
        tz = zoneinfo.ZoneInfo(timezone)
    except Exception:
        raise HTTPException(status_code=400, detail=f"ไม่รู้จัก timezone: {timezone}")

    dt_local = dt_local.replace(tzinfo=tz)
    dt_utc = dt_local.astimezone(zoneinfo.ZoneInfo("UTC"))

    weekday_th = DAYS_TH[dt_local.weekday()]

    result = {
        "date": date,
        "time": time or "00:00",
        "timezone": timezone,
        "weekday": weekday_th,
        "resolved_gregorian": d.isoformat(),
        "calendar": cal,
        "local_datetime": dt_local.isoformat(),
        "utc_datetime": dt_utc.isoformat(),
    }

    # ถ้าผู้ใช้ส่งชื่อสถานที่มา (ยังไม่ใช้คำนวณ แต่เก็บไว้)
    if place:
        result["place"] = place

    return JSONResponse(content=result)
