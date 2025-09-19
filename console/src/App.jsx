import React, { useState } from 'react'
const GATEWAY = 'http://localhost:8080'
export default function App(){
  const [messageId,setMessageId]=useState('11111111-1111-1111-1111-111111111111')
  const [status,setStatus]=useState(null)
  const [detail,setDetail]=useState(null)
  const [ledger,setLedger]=useState([])
  const [busy,setBusy]=useState(false)
  const register=async()=>{
    await fetch(`${GATEWAY}/v1/nodes/register`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({owner:'alice',endpoint:'http://example.com/a',biometricEnabled:true})})
    await fetch(`${GATEWAY}/v1/nodes/register`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({owner:'bob',endpoint:'http://example.com/b',biometricEnabled:false})})
    alert('Registered 2 demo nodes.')
  }
  const send=async()=>{
    setBusy(true)
    try{
      const res=await fetch(`${GATEWAY}/v1/messages`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        messageId,timestamp:new Date().toISOString(),fromNode:'node-1',toNode:'node-2',
        payload:{inputType:'sysA.v1',targetType:'sysB.v1',content:{first_name:'Jane',last_name:'Doe',phone:'(555) 111-2222'}},
        policy:{confidentiality:'internal',integrity:'high',retentionDays:30,allowLLMTransform:false,allowCrossChain:false},
        metadata:{traceId:'console'},signature:'demo-sig'})})
      const data=await res.json(); setStatus(data)
    } finally { setBusy(false) }
  }
  const check=async()=>{
    const r=await fetch(`${GATEWAY}/v1/messages/${messageId}/detail`)
    const d=await r.json(); setDetail(d)
  }
  const loadLedger=async()=>{
    const r=await fetch(`${GATEWAY}/v1/ledger/entries?limit=10`)
    const d=await r.json(); setLedger(d)
  }
  return (<div>
    <h1>AIIP Console</h1>
    <div className='card'><div className='row'>
      <button onClick={register}>Register nodes</button>
      <input value={messageId} onChange={e=>setMessageId(e.target.value)} style={{minWidth:'360px'}} />
      <button disabled={busy} onClick={send}>{busy?'Sending...':'Send demo message'}</button>
      <button onClick={check}>Check status</button>
      <button onClick={loadLedger}>Load ledger</button>
    </div></div>
    {status && <div className='card'><b>Status</b><pre>{JSON.stringify(status,null,2)}</pre></div>}
    {detail && <div className='card'><b>Message Detail</b><pre>{JSON.stringify(detail,null,2)}</pre></div>}
    {!!ledger.length && <div className='card'><b>Recent Ledger Entries</b>
      <table><thead><tr><th>Round</th><th>EntryId</th><th>Digest</th><th>Signatures (Ed25519 b64)</th></tr></thead>
        <tbody>{ledger.map(e=>(<tr key={e.entryId}><td>{e.round}</td><td><code>{e.entryId}</code></td><td><code>{e.messageDigest}</code></td><td style={{maxWidth:'500px'}}><code>{e.signatures.join(', ')}</code></td></tr>))}</tbody>
      </table></div>}
  </div>)
}
