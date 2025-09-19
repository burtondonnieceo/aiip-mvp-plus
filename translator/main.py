from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="AIIP Translator", version="0.2.0")

class TranslateReq(BaseModel):
    input: Dict[str, Any]
    inputType: str
    targetType: str

@app.get("/health")
def health():
    return {"status":"ok"}

def map_sysA_to_sysB(inp: Dict[str, Any]) -> Dict[str, Any]:
    first = (inp.get("first_name","") or "").strip()
    last = (inp.get("last_name","") or "").strip()
    full = (first + " " + last).strip()
    phone = (inp.get("phone","") or "")
    digits = "".join(c for c in phone if c.isdigit())
    tel = f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:]}" if len(digits)==10 else digits
    return {"fullName": full, "tel": tel, "source":"sysA.v1"}

@app.post("/v1/translate")
def translate(req: TranslateReq):
    if req.inputType == "sysA.v1" and req.targetType == "sysB.v1":
        return {"output": map_sysA_to_sysB(req.input), "traceId": "trace-demo"}
    return {"output": req.input, "traceId": "trace-demo"}
