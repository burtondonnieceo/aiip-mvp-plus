from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx, hashlib, json, os

TRANSLATOR_URL = os.getenv("TRANSLATOR_URL", "http://localhost:8081")
LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8082")

app = FastAPI(title="AIIP Gateway", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Policy(BaseModel):
    confidentiality: str
    integrity: str
    retentionDays: int
    allowLLMTransform: bool = False
    allowCrossChain: bool = False

class Message(BaseModel):
    messageId: str
    timestamp: str
    fromNode: str
    toNode: str
    payload: Dict[str, Any]
    policy: Policy
    metadata: Optional[Dict[str, str]] = None
    signature: str

class NodeReg(BaseModel):
    owner: str
    endpoint: str
    biometricEnabled: bool

class SendMessageResponse(BaseModel):
    messageId: str
    status: str
    ledgerEntryId: Optional[str] = None

MESSAGES: Dict[str, Dict[str, Any]] = {}
NODES: Dict[str, Dict[str, Any]] = {}
NODE_COUNTER = 0

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/v1/nodes/register")
def register_node(n: NodeReg):
    global NODE_COUNTER
    NODE_COUNTER += 1
    node_id = f"node-{NODE_COUNTER}"
    NODES[node_id] = n.model_dump()
    return {"nodeId": node_id}

@app.post("/v1/messages", response_model=SendMessageResponse)
def submit_message(msg: Message):
    MESSAGES[msg.messageId] = {"status":"queued", "payload": msg.payload}
    try:
        input_payload = msg.payload.get("content", {})
        input_type = msg.payload.get("inputType", "sysA.v1")
        target_type = msg.payload.get("targetType", "sysB.v1")
        with httpx.Client(timeout=10.0) as client:
            tr = client.post(f"{TRANSLATOR_URL}/v1/translate", json={
                "input": input_payload, "inputType": input_type, "targetType": target_type
            })
        tr.raise_for_status()
        translated = tr.json().get("output", {})
        MESSAGES[msg.messageId]["status"] = "translated"
        MESSAGES[msg.messageId]["translated"] = translated
    except Exception as e:
        MESSAGES[msg.messageId]["status"] = "error"
        raise HTTPException(status_code=502, detail=f"Translator error: {e}")
    digest = hashlib.sha256(json.dumps(translated, sort_keys=True).encode()).hexdigest()
    try:
        with httpx.Client(timeout=10.0) as client:
            lr = client.post(f"{LEDGER_URL}/v1/ledger/commit", json={
                "messageId": msg.messageId, "digest": digest
            })
        lr.raise_for_status()
        entry = lr.json()
        MESSAGES[msg.messageId]["status"] = "delivered"
        MESSAGES[msg.messageId]["ledgerEntryId"] = entry.get("entryId")
        MESSAGES[msg.messageId]["ledger"] = entry
    except Exception as e:
        MESSAGES[msg.messageId]["status"] = "error"
        raise HTTPException(status_code=502, detail=f"Ledger error: {e}")
    return SendMessageResponse(messageId=msg.messageId, status=MESSAGES[msg.messageId]["status"], ledgerEntryId=MESSAGES[msg.messageId]["ledgerEntryId"])

@app.get("/v1/messages/{message_id}", response_model=SendMessageResponse)
def get_message_status(message_id: str):
    if message_id not in MESSAGES:
        raise HTTPException(status_code=404, detail="Unknown messageId")
    rec = MESSAGES[message_id]
    return SendMessageResponse(messageId=message_id, status=rec.get("status"), ledgerEntryId=rec.get("ledgerEntryId"))

@app.get("/v1/messages/{message_id}/detail")
def get_message_detail(message_id: str):
    if message_id not in MESSAGES:
        raise HTTPException(status_code=404, detail="Unknown messageId")
    rec = MESSAGES[message_id]
    return {"messageId": message_id, **rec}

@app.get("/v1/ledger/entries")
def passthrough_ledger(limit: int = Query(20, ge=1, le=100)):
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{LEDGER_URL}/v1/ledger/entries", params={"limit": limit})
    r.raise_for_status()
    return r.json()
