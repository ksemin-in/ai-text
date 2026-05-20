from flask import Flask, request, jsonify, render_template_string
import requests
import json
import re

app = Flask(__name__)

GROQ_API_KEY = "your_groq_api_key_here"

SYSTEM_PROMPT = """You are an expert contract analyst. Analyze the provided contract text and extract structured information. Return ONLY a valid JSON object with NO markdown, NO backticks, NO extra text.

The JSON must follow this exact schema:
{
  "summary": "2-3 sentence executive summary",
  "contractType": "type of contract",
  "parties": [{"name": "party name", "role": "their role"}],
  "keyDates": [{"label": "date label", "date": "date value", "description": "context", "urgency": "high|medium|low"}],
  "deadlines": [{"task": "what must be done", "deadline": "when", "consequence": "if missed", "urgency": "high|medium|low"}],
  "penalties": [{"trigger": "what causes penalty", "amount": "penalty amount", "severity": "high|medium|low"}],
  "importantClauses": [{"title": "clause name", "summary": "explanation", "importance": "high|medium|low"}],
  "riskAnalysis": {
    "overallRisk": "HIGH|MEDIUM|LOW",
    "riskScore": 0,
    "risks": [{"category": "category", "description": "description", "severity": "high|medium|low", "mitigation": "suggestion"}]
  },
  "obligations": [{"party": "party name", "obligation": "what they must do", "timeframe": "when"}],
  "financialTerms": {"totalValue": "value", "paymentSchedule": "terms", "currency": "currency"},
  "terminationConditions": ["condition 1"],
  "redFlags": ["critical concern 1"]
}"""

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>ContractIQ - AI Contract Intelligence</title>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet"/>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#0a0a0f;color:#e8e8f0;font-family:'DM Sans',sans-serif;min-height:100vh;background-image:radial-gradient(ellipse at 15% 0%,rgba(124,58,237,.14) 0%,transparent 55%),radial-gradient(ellipse at 85% 100%,rgba(59,130,246,.09) 0%,transparent 55%)}
    .header{border-bottom:1px solid rgba(255,255,255,.06);padding:16px 28px;display:flex;align-items:center;justify-content:space-between}
    .logo-wrap{display:flex;align-items:center;gap:11px}
    .logo-icon{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#7c3aed,#3b82f6);display:flex;align-items:center;justify-content:center;font-size:16px}
    .logo-title{font-size:16px;font-weight:900;font-family:'Syne',sans-serif;letter-spacing:-.02em}
    .logo-sub{font-size:9px;color:rgba(255,255,255,.3);letter-spacing:.1em}
    .status-dot{width:6px;height:6px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;display:inline-block;margin-right:6px}
    .status-txt{font-size:10px;color:rgba(255,255,255,.25);letter-spacing:.06em}
    .main{max-width:1200px;margin:0 auto;padding:24px 20px;display:grid;grid-template-columns:380px 1fr;gap:20px;align-items:start}
    @media(max-width:800px){.main{grid-template-columns:1fr}}
    .upload-zone{border:2px dashed rgba(255,255,255,.1);border-radius:13px;padding:14px 18px;cursor:pointer;background:rgba(255,255,255,.02);transition:all .2s;margin-bottom:10px;text-align:center}
    .upload-zone:hover{border-color:#7c3aed;background:rgba(124,58,237,.06)}
    .upload-icon{font-size:20px;margin-bottom:4px}
    .upload-txt{font-size:11px;color:rgba(255,255,255,.4)}
    textarea{width:100%;height:300px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.09);border-radius:13px;color:#d4d4e8;font-size:11px;font-family:'DM Mono',monospace;padding:14px;resize:vertical;line-height:1.7;outline:none;transition:border-color .2s}
    textarea:focus{border-color:rgba(124,58,237,.5)}
    .btn-row{display:flex;gap:8px;margin-top:10px}
    .btn-analyze{flex:1;padding:12px 18px;border-radius:11px;border:none;cursor:pointer;background:linear-gradient(135deg,#7c3aed,#5b21b6);color:#fff;font-size:13px;font-weight:700;font-family:'Syne',sans-serif;letter-spacing:.04em;box-shadow:0 4px 18px rgba(124,58,237,.38);transition:opacity .2s}
    .btn-analyze:disabled{opacity:.45;cursor:not-allowed}
    .btn-sample{padding:12px 14px;border-radius:11px;border:1px solid rgba(255,255,255,.1);background:transparent;color:rgba(255,255,255,.4);font-size:12px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all .2s}
    .btn-sample:hover{border-color:rgba(255,255,255,.25);color:rgba(255,255,255,.7)}
    .error-box{margin-top:10px;padding:10px 14px;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);border-radius:9px;color:#fca5a5;font-size:12px}
    .features{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:18px}
    .feat{background:rgba(255,255,255,.03);border-radius:10px;padding:12px 8px;border:1px solid rgba(255,255,255,.06);text-align:center}
    .feat-icon{font-size:16px;margin-bottom:4px}
    .feat-label{font-size:10px;font-weight:600;color:rgba(255,255,255,.65)}
    .contract-hdr{background:linear-gradient(135deg,rgba(124,58,237,.14),rgba(59,130,246,.09));border-radius:15px;padding:20px;margin-bottom:12px;border:1px solid rgba(124,58,237,.2)}
    .c-type-label{font-size:9px;color:rgba(255,255,255,.35);letter-spacing:.12em;margin-bottom:4px}
    .c-type{font-size:19px;font-weight:900;font-family:'Syne',sans-serif;margin-bottom:9px}
    .c-summary{font-size:12px;color:rgba(255,255,255,.62);line-height:1.65;margin-bottom:11px}
    .parties{display:flex;gap:6px;flex-wrap:wrap}
    .party-chip{background:rgba(255,255,255,.07);border-radius:6px;padding:4px 10px;font-size:11px}
    .party-role{color:rgba(255,255,255,.4)}
    .red-flags-box{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.22);border-radius:12px;padding:13px 16px;margin-bottom:12px}
    .rf-title{color:#fca5a5;font-size:10px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:9px}
    .rf-item{color:#fca5a5;font-size:12px;margin-bottom:5px;display:flex;gap:8px}
    .tabs{display:flex;gap:3px;background:rgba(255,255,255,.03);border-radius:11px;padding:3px;border:1px solid rgba(255,255,255,.06);margin-bottom:12px}
    .tab{flex:1;padding:7px 4px;border-radius:8px;border:none;cursor:pointer;background:transparent;color:rgba(255,255,255,.38);font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;transition:all .18s;font-family:'DM Sans',sans-serif;display:flex;flex-direction:column;align-items:center;gap:2px}
    .tab.active{background:rgba(124,58,237,.55);color:#fff}
    .tab-icon{font-size:13px}
    .tab-content{display:none;max-height:440px;overflow-y:auto;padding-right:2px}
    .tab-content.active{display:block}
    .section{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:18px;margin-bottom:12px}
    .section-title{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:14px}
    .card{background:rgba(255,255,255,.04);border-radius:9px;padding:11px 13px;border:1px solid rgba(255,255,255,.06);margin-bottom:7px}
    .badge{display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
    .badge-high{background:rgba(239,68,68,.12);color:#ef4444;border:1px solid rgba(239,68,68,.25)}
    .badge-medium{background:rgba(245,158,11,.12);color:#f59e0b;border:1px solid rgba(245,158,11,.25)}
    .badge-low{background:rgba(16,185,129,.12);color:#10b981;border:1px solid rgba(16,185,129,.25)}
    .badge-dot{width:5px;height:5px;border-radius:50%;background:currentColor;display:inline-block}
    .risk-overview{border-radius:12px;padding:14px 16px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
    .fin-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:11px}
    .fin-card{border-radius:11px;padding:13px 15px}
    .fin-label{font-size:9px;color:rgba(255,255,255,.38);margin-bottom:5px;letter-spacing:.08em}
    .fin-val{font-size:17px;font-weight:900;font-family:'Syne',sans-serif}
    .loading-wrap{text-align:center;padding:48px 20px;color:rgba(255,255,255,.4)}
    .spinner{width:28px;height:28px;border:3px solid rgba(255,255,255,.08);border-top-color:#7c3aed;border-radius:50%;animation:spin .7s linear infinite;margin:0 auto 12px}
    @keyframes spin{to{transform:rotate(360deg)}}
    .loading-txt{font-size:13px;margin-bottom:6px}
    .loading-sub{font-size:11px;color:rgba(255,255,255,.25)}
    ::-webkit-scrollbar{width:3px}
    ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:3px}
  </style>
</head>
<body>

<div class="header">
  <div class="logo-wrap">
    <div class="logo-icon">⚖️</div>
    <div>
      <div class="logo-title">ContractIQ</div>
      <div class="logo-sub">AI CONTRACT INTELLIGENCE</div>
    </div>
  </div>
  <div><span class="status-dot"></span><span class="status-txt">POWERED BY GROQ + LLAMA</span></div>
</div>

<div class="main">
  <div class="input-panel">
    <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
      <input type="file" id="fileInput" accept=".txt" style="display:none" onchange="loadFile(event)"/>
      <div class="upload-icon">📄</div>
      <div class="upload-txt">Drop <strong style="color:rgba(255,255,255,.75)">.txt</strong> file or click to upload</div>
    </div>
    <textarea id="contractText" placeholder="Paste your contract text here..."></textarea>
    <div class="btn-row">
      <button class="btn-analyze" id="analyzeBtn" onclick="analyze()">⚡ Analyze Contract</button>
      <button class="btn-sample" onclick="loadSample()">Sample</button>
    </div>
    <div id="errorBox" class="error-box" style="display:none"></div>
    <div class="features" id="featuresGrid">
      <div class="feat"><div class="feat-icon">📋</div><div class="feat-label">Summary</div></div>
      <div class="feat"><div class="feat-icon">📅</div><div class="feat-label">Dates</div></div>
      <div class="feat"><div class="feat-icon">⚠️</div><div class="feat-label">Risks</div></div>
      <div class="feat"><div class="feat-icon">💸</div><div class="feat-label">Penalties</div></div>
      <div class="feat"><div class="feat-icon">💰</div><div class="feat-label">Finance</div></div>
      <div class="feat"><div class="feat-icon">🚨</div><div class="feat-label">Red Flags</div></div>
    </div>
  </div>

  <div id="resultsPanel" style="display:none">
    <div id="loadingWrap" class="loading-wrap">
      <div class="spinner"></div>
      <div class="loading-txt">Analyzing your contract...</div>
      <div class="loading-sub">AI is reading every clause carefully</div>
    </div>
    <div id="analysisWrap" style="display:none"></div>
  </div>
</div>

<script>
const SAMPLE = `SERVICE AGREEMENT

This Service Agreement is entered into as of January 15, 2025, between TechCorp Solutions Inc. ("Service Provider") and GlobalRetail Ltd. ("Client").

1. SERVICES
Service Provider agrees to develop a custom e-commerce platform. Delivery due by June 30, 2025.

2. PAYMENT TERMS
Client shall pay USD 250,000:
- 30% on signing within 5 business days
- 40% on milestone completion April 15, 2025
- 30% on final delivery
Late payments incur 1.5% monthly penalty.

3. PENALTIES
Failure to deliver by June 30, 2025 results in $5,000/day liquidated damages, max $100,000.
Delay over 30 days allows termination and full refund demand.

4. CONFIDENTIALITY
5 years confidentiality obligation. Breach results in $500,000 damages.

5. TERMINATION
30 days written notice. Auto-renews unless 60-day notice before December 31, 2025.

6. GOVERNING LAW
New York law. Binding arbitration in NYC within 60 days.`;

function loadSample(){
  document.getElementById('contractText').value = SAMPLE;
}

function loadFile(e){
  const file = e.target.files[0];
  if(!file) return;
  const reader = new FileReader();
  reader.onload = ev => document.getElementById('contractText').value = ev.target.result;
  reader.readAsText(file);
}

async function analyze(){
  const text = document.getElementById('contractText').value.trim();
  if(!text){ alert('Please paste contract text first!'); return; }

  document.getElementById('errorBox').style.display='none';
  document.getElementById('resultsPanel').style.display='block';
  document.getElementById('loadingWrap').style.display='block';
  document.getElementById('analysisWrap').style.display='none';
  document.getElementById('featuresGrid').style.display='none';
  document.getElementById('analyzeBtn').disabled=true;
  document.getElementById('analyzeBtn').textContent='Analyzing...';

  try {
    const res = await fetch('/analyze',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({contract: text})
    });
    const data = await res.json();
    if(data.error) throw new Error(data.error);
    renderAnalysis(data);
  } catch(e){
    document.getElementById('errorBox').style.display='block';
    document.getElementById('errorBox').textContent = 'Error: ' + e.message;
    document.getElementById('loadingWrap').style.display='none';
    document.getElementById('featuresGrid').style.display='grid';
  }

  document.getElementById('analyzeBtn').disabled=false;
  document.getElementById('analyzeBtn').textContent='⚡ Analyze Contract';
}

function rc(l){
  if(!l) return '#6b7280';
  l=l.toLowerCase();
  return l==='high'?'#ef4444':l==='medium'?'#f59e0b':'#10b981';
}
function rb(l){
  if(!l) return 'rgba(107,114,128,.15)';
  l=l.toLowerCase();
  return l==='high'?'rgba(239,68,68,.1)':l==='medium'?'rgba(245,158,11,.1)':'rgba(16,185,129,.1)';
}
function badge(level){
  const l=(level||'low').toLowerCase();
  return `<span class="badge badge-${l}"><span class="badge-dot"></span>${l}</span>`;
}

function renderAnalysis(a){
  document.getElementById('loadingWrap').style.display='none';
  const riskC = rc(a.riskAnalysis?.overallRisk);

  let html = `
  <div class="contract-hdr">
    <div class="c-type-label">CONTRACT TYPE</div>
    <div class="c-type">${a.contractType||'Agreement'}</div>
    <div class="c-summary">${a.summary||''}</div>
    <div class="parties">${(a.parties||[]).map(p=>`<div class="party-chip"><span class="party-role">${p.role}: </span><strong>${p.name}</strong></div>`).join('')}</div>
  </div>`;

  if(a.redFlags?.length){
    html+=`<div class="red-flags-box">
      <div class="rf-title">🚨 Red Flags — Immediate Attention</div>
      ${a.redFlags.map(f=>`<div class="rf-item"><span style="color:#ef4444">▸</span>${f}</div>`).join('')}
    </div>`;
  }

  html+=`<div class="tabs">
    <button class="tab active" onclick="showTab('overview',this)"><span class="tab-icon">📋</span>Overview</button>
    <button class="tab" onclick="showTab('dates',this)"><span class="tab-icon">📅</span>Dates</button>
    <button class="tab" onclick="showTab('risks',this)"><span class="tab-icon">⚠️</span>Risks</button>
    <button class="tab" onclick="showTab('finance',this)"><span class="tab-icon">💰</span>Finance</button>
    <button class="tab" onclick="showTab('duties',this)"><span class="tab-icon">📌</span>Duties</button>
  </div>`;

  html+=`<div id="tab-overview" class="tab-content active">
    <div class="section">
      <div class="section-title">📌 Important Clauses</div>
      ${(a.importantClauses||[]).map(c=>`<div class="card"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px"><div><div style="font-size:13px;font-weight:600;margin-bottom:4px">${c.title}</div><div style="font-size:11px;color:rgba(255,255,255,.5);line-height:1.5">${c.summary}</div></div>${badge(c.importance)}</div></div>`).join('')}
    </div>
    <div class="section">
      <div class="section-title">🔚 Termination Conditions</div>
      ${(a.terminationConditions||[]).map(t=>`<div style="display:flex;gap:8px;margin-bottom:7px"><span style="color:#f59e0b;flex-shrink:0">◆</span><span style="font-size:12px;color:rgba(255,255,255,.65)">${t}</span></div>`).join('')}
    </div>
  </div>`;

  html+=`<div id="tab-dates" class="tab-content">
    <div class="section">
      <div class="section-title">📅 Key Dates</div>
      ${(a.keyDates||[]).map(d=>`<div class="card"><div style="display:flex;justify-content:space-between;align-items:flex-start"><div><div style="font-size:10px;color:rgba(255,255,255,.38);margin-bottom:3px">${d.label}</div><div style="font-size:14px;font-weight:800;color:#93c5fd;margin-bottom:3px;font-family:'Syne',sans-serif">${d.date}</div><div style="font-size:11px;color:rgba(255,255,255,.5)">${d.description}</div></div>${badge(d.urgency)}</div></div>`).join('')}
    </div>
    <div class="section">
      <div class="section-title">⏰ Deadlines</div>
      ${(a.deadlines||[]).map(d=>`<div class="card" style="border-left:3px solid ${rc(d.urgency)}"><div style="display:flex;justify-content:space-between;margin-bottom:5px"><div style="font-size:12px;font-weight:600">${d.task}</div>${badge(d.urgency)}</div><div style="font-size:11px;color:#93c5fd;margin-bottom:${d.consequence?4:0}px">📅 ${d.deadline}</div>${d.consequence?`<div style="font-size:11px;color:rgba(239,68,68,.8)">⚠ ${d.consequence}</div>`:''}</div>`).join('')}
    </div>
  </div>`;

  html+=`<div id="tab-risks" class="tab-content">
    <div class="risk-overview" style="background:${rb(a.riskAnalysis?.overallRisk)};border:1px solid ${riskC}30">
      <div><div style="font-size:9px;color:rgba(255,255,255,.38);letter-spacing:.1em;margin-bottom:4px">OVERALL RISK LEVEL</div><div style="font-size:24px;font-weight:900;font-family:'Syne',sans-serif;color:${riskC}">${a.riskAnalysis?.overallRisk||'N/A'}</div></div>
      <div><div style="font-size:38px;font-weight:900;font-family:'Syne',sans-serif;color:${riskC};line-height:1">${a.riskAnalysis?.riskScore||0}</div><div style="font-size:10px;color:rgba(255,255,255,.28);text-align:right">/ 100</div></div>
    </div>
    <div class="section">
      <div class="section-title">⚠️ Risk Details</div>
      ${(a.riskAnalysis?.risks||[]).map(r=>`<div class="card" style="border-left:3px solid ${rc(r.severity)}"><div style="display:flex;justify-content:space-between;margin-bottom:5px"><span style="font-size:10px;font-weight:700;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:.07em">${r.category}</span>${badge(r.severity)}</div><div style="font-size:12px;margin-bottom:${r.mitigation?7:0}px;color:rgba(255,255,255,.75)">${r.description}</div>${r.mitigation?`<div style="font-size:11px;color:rgba(16,185,129,.85);padding:5px 9px;background:rgba(16,185,129,.07);border-radius:6px">💡 ${r.mitigation}</div>`:''}</div>`).join('')}
    </div>
    <div class="section">
      <div class="section-title">💸 Penalties & Damages</div>
      ${(a.penalties||[]).map(p=>`<div class="card"><div style="display:flex;justify-content:space-between;margin-bottom:5px"><span style="font-size:12px;color:rgba(255,255,255,.65)">${p.trigger}</span>${badge(p.severity)}</div><div style="font-size:14px;font-weight:700;color:#fca5a5;font-family:'Syne',sans-serif">${p.amount}</div></div>`).join('')}
    </div>
  </div>`;

  html+=`<div id="tab-finance" class="tab-content">
    <div class="section">
      <div class="section-title">💰 Financial Summary</div>
      <div class="fin-grid">
        <div class="fin-card" style="background:rgba(16,185,129,.09);border:1px solid rgba(16,185,129,.18)"><div class="fin-label">TOTAL VALUE</div><div class="fin-val" style="color:#6ee7b7">${a.financialTerms?.totalValue||'N/A'}</div></div>
        <div class="fin-card" style="background:rgba(59,130,246,.09);border:1px solid rgba(59,130,246,.18)"><div class="fin-label">CURRENCY</div><div class="fin-val" style="color:#93c5fd">${a.financialTerms?.currency||'N/A'}</div></div>
      </div>
      ${a.financialTerms?.paymentSchedule?`<div style="font-size:12px;color:rgba(255,255,255,.55);padding:11px 13px;background:rgba(255,255,255,.04);border-radius:8px;line-height:1.65">${a.financialTerms.paymentSchedule}</div>`:''}
    </div>
  </div>`;

  html+=`<div id="tab-duties" class="tab-content">
    <div class="section">
      <div class="section-title">📋 Party Obligations</div>
      ${(a.obligations||[]).map(o=>`<div class="card"><div style="font-size:9px;font-weight:700;color:#a78bfa;letter-spacing:.09em;text-transform:uppercase;margin-bottom:4px">${o.party}</div><div style="font-size:12px;color:rgba(255,255,255,.75);margin-bottom:${o.timeframe?5:0}px">${o.obligation}</div>${o.timeframe?`<div style="font-size:11px;color:rgba(255,255,255,.35)">⏱ ${o.timeframe}</div>`:''}</div>`).join('')}
    </div>
  </div>`;

  document.getElementById('analysisWrap').innerHTML = html;
  document.getElementById('analysisWrap').style.display='block';
}

function showTab(name, btn){
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  btn.classList.add('active');
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        contract_text = data.get('contract', '')

        if not contract_text:
            return jsonify({'error': 'No contract text provided'}), 400

        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': f'Analyze this contract:\n\n{contract_text}'}
                ],
                'temperature': 0.1,
                'max_tokens': 4000
            },
            timeout=60
        )

        response_data = response.json()

        if 'error' in response_data:
            return jsonify({'error': response_data['error']['message']}), 500

        raw = response_data['choices'][0]['message']['content'].strip()
        clean = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(clean)
        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({'error': 'AI returned invalid response. Please try again.'}), 500
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("  ContractIQ - AI Contract Intelligence")
    print("  Powered by Groq + LLaMA 3.3 70B")
    print("  Open: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
