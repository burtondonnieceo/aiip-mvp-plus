# AIIP MVP Plus (AIIP 2.0-ready demo)
Services:
- Gateway (FastAPI) – accepts message → deterministic translate → commit digest to PoHG ledger
- Translator (FastAPI) – SystemA→SystemB field mapping
- Ledger (FastAPI) – append-only log with 3 Ed25519 validator signatures
- Console (React+Vite) – buttons to drive the flow
Run (Codespaces):
  1) Translator:  uvicorn main:app --host 0.0.0.0 --port 8081
  2) Ledger:      uvicorn main:app --host 0.0.0.0 --port 8082
  3) Gateway:     uvicorn main:app --host 0.0.0.0 --port 8080
  4) Console:     npm run dev -- --host  (port 5173)
