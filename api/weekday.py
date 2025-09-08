from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

days = ["จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์"]

@app.get("/api/weekday")
def get_weekday(date: str):
    """
    ตรวจสอบวันจริงจากวันที่
    date format: DD/MM/YYYY (พ.ศ. หรือ ค.ศ.)
    """
    d = datetime.strptime(date, "%d/%m/%Y")
    if d.year > 2400:  # ถ้าเป็น พ.ศ.
        d = d.replace(year=d.year - 543)
    weekday = days[d.weekday()]
    return JSONResponse(content={"date": date, "weekday": weekday})

