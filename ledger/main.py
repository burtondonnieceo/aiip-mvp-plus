from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import time, uuid, base64
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder

app = FastAPI(title="AIIP PoHG-Ledger (Ed25519 demo)", version="0.2.0")

class CommitReq(BaseModel):
    messageId: str
    digest: str

LEDGER: List[Dict[str, Any]] = []
ROUND = 0

DEMO_SEEDS = [
    bytes.fromhex("0101010101010101010101010101010101010101010101010101010101010101"),
    bytes.fromhex("0202020202020202020202020202020202020202020202020202020202020202"),
    bytes.fromhex("0303030303030303030303030303030303030303030303030303030303030303"),
]
SIGNERS = [SigningKey(seed) for seed in DEMO_SEEDS]
PUBKEYS_B64 = [base64.b64encode(s.verify_key.encode()).decode() for s in SIGNERS]

@app.get("/health")
def health():
    return {"status":"ok","validators":PUBKEYS_B64}

@app.post("/v1/ledger/commit")
def commit(req: CommitReq):
    global ROUND
    ROUND += 1
    entry_id = str(uuid.uuid4())
    msg_bytes = req.digest.encode()
    signatures = []
    for s in SIGNERS:
        sig = s.sign(msg_bytes, encoder=RawEncoder).signature
        signatures.append(base64.b64encode(sig).decode())
    entry = {
        "entryId": entry_id,
        "round": ROUND,
        "messageId": req.messageId,
        "messageDigest": req.digest,
        "validatorSet": PUBKEYS_B64,
        "signatures": signatures,
        "pqcSignature": None,
        "committedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    LEDGER.append(entry)
    return entry

@app.get("/v1/ledger/entries")
def list_entries(limit: int = Query(20, ge=1, le=100)):
    return LEDGER[-limit:][::-1]
