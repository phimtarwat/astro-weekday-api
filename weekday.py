from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import zoneinfo
from typing import Optional

# เพิ่ม import สำหรับโหราศาสตร์
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos


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
# Endpoint เดิม (ดูวันจากวันที่)
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
# 🪐 Endpoint สำหรับโหราศาสตร์เบื้องต้น
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


# ------------------------------
# 🪐 Endpoint ใหม่: คำนวณดวงดาวจริง (ใช้ flatlib)
# ------------------------------
@app.get("/api/astro-chart")
def get_astro_chart(
    date: str,
    time: str,
    timezone: str = "Asia/Bangkok",
    lat: float = 13.75,
    lon: float = 100.50
):
    """
    คำนวณตำแหน่งดวงดาว (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Ascendant)
    ตัวอย่าง:
      /api/astro-chart?date=24/11/2514&time=11:00&timezone=Asia/Bangkok&lat=13.75&lon=100.5
    """
    d, cal = parse_ddmmyyyy_th(date)
    from datetime import datetime as dt
    tz = zoneinfo.ZoneInfo(timezone)
    offset_hours = dt(d.year, d.month, d.day, int(time[:2]), int(time[3:]), tzinfo=tz).utcoffset().total_seconds() / 3600.0

    pos = GeoPos(lat, lon)
    t = Datetime(f"{d.year}/{d.month:02d}/{d.day:02d}", time, offset=offset_hours)
    chart = Chart(t, pos)

    planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    result = {p: {
        "sign": chart.get(p).sign,
        "lon": round(chart.get(p).lon, 2)
    } for p in planets}

    result["Ascendant"] = {
        "sign": chart.get("Asc").sign,
        "lon": round(chart.get("Asc").lon, 2)
    }

    return JSONResponse(content={
        "input": {"date": date, "time": time, "timezone": timezone, "lat": lat, "lon": lon},
        "planets": result
    })
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("weekday:app", host="0.0.0.0", port=8000)
