from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import zoneinfo
from typing import Optional
import os

# ✅ ใช้ flatlib-lite (ไม่ต้องใช้ swisseph)
from flatlib import chart, const, geo, datetime as flatdatetime

app = FastAPI()

DAYS_TH = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]


# ------------------------------
# แปลงวันที่ พ.ศ./ค.ศ.
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
            d = d.replace(year=y, day=28)
    return d, calendar


# ------------------------------
# Root Endpoint
# ------------------------------
@app.get("/")
def root():
    return {"message": "Astro Weekday API (lite) is running 🚀"}


# ------------------------------
# Endpoint: ตรวจสอบวันจากวันที่
# ------------------------------
@app.get("/api/weekday")
def get_weekday(date: str):
    """ตรวจสอบวันจริงจากวันที่ (DD/MM/YYYY)"""
    d, cal = parse_ddmmyyyy_th(date)
    weekday = DAYS_TH[d.weekday()]
    return JSONResponse(content={
        "date": date,
        "weekday": weekday,
        "resolved_gregorian": d.isoformat(),
        "calendar": cal
    })


# ------------------------------
# Endpoint: ตรวจสอบวัน + เวลา + timezone + สถานที่
# ------------------------------
@app.get("/api/astro-weekday")
def get_astro_weekday(
    date: str,
    time: Optional[str] = None,
    timezone: Optional[str] = "Asia/Bangkok",
    place: Optional[str] = None
):
    """ตรวจสอบวันจริง + เวลา + timezone + สถานที่เกิด"""
    d, cal = parse_ddmmyyyy_th(date)
    if time:
        try:
            t = datetime.strptime(time, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="รูปแบบเวลาไม่ถูกต้อง (ต้องเป็น HH:MM)")
    else:
        t = datetime.min.time()

    try:
        tz = zoneinfo.ZoneInfo(timezone)
    except Exception:
        raise HTTPException(status_code=400, detail=f"ไม่รู้จัก timezone: {timezone}")

    dt_local = datetime.combine(d, t).replace(tzinfo=tz)
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
    if place:
        result["place"] = place
    return JSONResponse(content=result)


# ------------------------------
# Endpoint: คำนวณตำแหน่งดวงดาว (flatlib-lite)
# ------------------------------
@app.get("/api/astro-chart")
def get_astro_chart(
    date: str,
    time: str,
    timezone: str = "Asia/Bangkok",
    lat: float = 13.75,
    lon: float = 100.50
):
    """คำนวณตำแหน่งดวงดาว (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Ascendant)"""
    d, cal = parse_ddmmyyyy_th(date)
    tz = zoneinfo.ZoneInfo(timezone)
    dt_local = datetime.combine(d, datetime.strptime(time, "%H:%M").time()).replace(tzinfo=tz)
    offset_hours = dt_local.utcoffset().total_seconds() / 3600.0

    pos = geo.GeoPos(lat, lon)
    t = flatdatetime.Datetime(f"{d.year}/{d.month:02d}/{d.day:02d}", time, offset=offset_hours)
    c = chart.Chart(t, pos)

    planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    result = {p: {
        "sign": c.get(p).sign,
        "lon": round(c.get(p).lon, 2)
    } for p in planets}

    result["Ascendant"] = {
        "sign": c.get("Asc").sign,
        "lon": round(c.get("Asc").lon, 2)
    }

    return JSONResponse(content={
        "input": {"date": date, "time": time, "timezone": timezone, "lat": lat, "lon": lon},
        "planets": result
    })


# ------------------------------
# ✅ Endpoint: ให้ดาวน์โหลด openapi.yaml ได้โดยตรง
# ------------------------------
@app.get("/openapi.yaml")
def get_openapi_yaml():
    """เสิร์ฟไฟล์ schema ให้ Custom GPT โหลด"""
    file_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/yaml")
    else:
        raise HTTPException(status_code=404, detail="openapi.yaml not found")


# ------------------------------
# Run ในเครื่อง (dev mode)
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("weekday:app", host="0.0.0.0", port=8000)
