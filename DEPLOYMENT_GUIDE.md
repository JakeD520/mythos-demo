# MythOS Demo - Remote Deployment Architecture

## 🏗️ Current Stack Overview

### **Core Services Architecture**
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Island Scorer     │    │    Prose Store      │    │      Editor         │
│   Port: 8000        │    │    Port: 8001       │    │    Port: 8002       │
│   FastAPI + CORS    │    │   FastAPI + CORS    │    │   FastAPI + CORS    │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      │
                              ┌─────────────────────┐
                              │  Client HTML Demo   │
                              │  working_demo.html  │
                              │  JavaScript/CORS    │
                              └─────────────────────┘
```

### **Technology Stack**
- **Backend**: Python 3.11+ with FastAPI
- **AI/ML**: SentenceTransformers (all-MiniLM-L6-v2), FAISS HNSW indexing
- **Frontend**: Vanilla HTML/CSS/JavaScript with WebSocket-less HTTP polling
- **CORS**: Enabled for cross-origin requests (critical for remote hosting)

---

## 🚀 Remote Hosting Requirements

### **1. Server Infrastructure**
```yaml
Minimum Requirements:
  CPU: 4 cores (for transformer models)
  RAM: 8GB (4GB for models + 4GB system)
  Storage: 10GB (models + indices + logs)
  Network: Static IP with ports 8000-8002 accessible
  OS: Linux (Ubuntu 20.04+ recommended)
```

### **2. Dependencies & Environment**
```bash
# Python environment
Python 3.11+
pip install -r requirements.txt

# Key packages:
- fastapi>=0.104.0
- uvicorn>=0.24.0
- sentence-transformers>=2.2.2
- faiss-cpu>=1.7.4
- numpy>=1.24.0
- pydantic>=2.4.0
```

### **3. File Structure to Deploy**
```
mythos_demo/
├── services/
│   ├── island_scorer/          # PRIMARY SERVICE (Port 8000)
│   │   ├── app.py             # Main FastAPI application
│   │   ├── build.py           # World building logic
│   │   ├── score.py           # Scoring algorithm 
│   │   ├── models.py          # Pydantic data models
│   │   └── __init__.py
│   ├── prose_store/           # Secondary (Port 8001)
│   └── editor/                # Secondary (Port 8002)
├── corpus/                    # CRITICAL: Pre-built worlds
│   ├── greek_myth/            # 13 mythology chunks
│   ├── fantasy_realm/         # 9 fantasy chunks  
│   └── vampire_cyberpunk/     # 9 cyberpunk chunks
├── worlds/                    # CRITICAL: FAISS indices
│   ├── greek_myth.index       # Pre-computed embeddings
│   ├── fantasy_realm.index
│   └── vampire_cyberpunk.index
└── working_demo.html          # Client demo (can be served separately)
```

---

## 🔧 Deployment Steps

### **Phase 1: Core Service (Island Scorer)**
```bash
# 1. Upload core files
scp -r services/island_scorer/ user@remote-server:/opt/mythos/
scp -r corpus/ user@remote-server:/opt/mythos/
scp -r worlds/ user@remote-server:/opt/mythos/

# 2. Install dependencies
ssh user@remote-server
cd /opt/mythos
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sentence-transformers faiss-cpu numpy pydantic

# 3. Start Island Scorer (primary service)
cd /opt/mythos
python -m services.island_scorer.app
# Should start on http://0.0.0.0:8000
```

### **Phase 2: Client Demo Hosting**
```bash
# Option A: Serve from same server
python -m http.server 8080 --directory /path/to/working_demo.html

# Option B: Use nginx/apache to serve static HTML
# Option C: Host on separate CDN/static hosting (GitHub Pages, Netlify, etc.)
```

### **Phase 3: Update Client Configuration**
```javascript
// In working_demo.html, update the server URL:
this.islandScorerUrl = 'http://YOUR-REMOTE-SERVER-IP:8000';
// Or use domain name:
this.islandScorerUrl = 'https://mythos-demo.your-domain.com';
```

---

## 🌐 Production Considerations

### **1. Security & Access Control**
```yaml
Firewall Rules:
  - Port 8000: Open (Island Scorer API)
  - Port 8001-8002: Optional (if deploying full stack)
  - Port 80/443: Open (if serving HTML)
  - SSH: Restricted to admin IPs

CORS Configuration:
  - origins: ["*"] # For demo (restrict in production)
  - methods: ["GET", "POST"]
  - headers: ["Content-Type"]
```

### **2. Process Management (Production)**
```bash
# Use systemd for auto-restart
cat > /etc/systemd/system/mythos-island-scorer.service << EOF
[Unit]
Description=MythOS Island Scorer Service
After=network.target

[Service]
Type=simple
User=mythos
WorkingDirectory=/opt/mythos
Environment=PATH=/opt/mythos/venv/bin
ExecStart=/opt/mythos/venv/bin/python -m services.island_scorer.app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable mythos-island-scorer
systemctl start mythos-island-scorer
```

### **3. Load Balancing & Scaling**
```yaml
# For high traffic, consider:
Reverse Proxy: nginx/Apache in front of FastAPI
Load Balancer: Multiple Island Scorer instances
Caching: Redis for frequent queries
CDN: For static HTML/CSS/JS assets
```

---

## 📊 Monitoring & Health Checks

### **Health Endpoints**
```bash
# Island Scorer health check
curl http://YOUR-SERVER:8000/health
# Expected: {"status": "healthy", "service": "island_scorer"}

# Test scoring functionality  
curl -X POST http://YOUR-SERVER:8000/score \
  -H "Content-Type: application/json" \
  -d '{"world_id": "greek_myth", "text": "Zeus ruled from Olympus"}'
```

### **Log Monitoring**
```bash
# Service logs
journalctl -u mythos-island-scorer -f

# Application logs (add to app.py)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

---

## 🔒 Demo Sharing Strategy

### **Option A: Direct Server Access**
```
Share URL: http://YOUR-SERVER-IP:8080/working_demo.html
Pros: Full control, real-time updates
Cons: Exposes server IP
```

### **Option B: Static Demo + API**
```
Demo URL: https://your-github-pages.io/mythos-demo.html
API URL: https://api.your-domain.com:8000
Pros: Professional appearance, API abstraction
Cons: Requires domain/SSL setup
```

### **Option C: Dockerized Deployment**
```dockerfile
# Dockerfile for easy deployment
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "services.island_scorer.app"]
```

---

## 🎯 Critical Success Factors

### **1. Pre-built World Indices**
- **MUST** copy the `worlds/` directory with pre-computed FAISS indices
- Building indices takes 5-10 minutes per world on first startup
- Indices contain the 384-dimensional embeddings for all reference chunks

### **2. CORS Configuration**
- Essential for browser-based demo to access remote API
- Current config allows all origins (good for demo, restrict for production)

### **3. Content-Agnostic Validation**
- The three worlds (greek_myth, fantasy_realm, vampire_cyberpunk) prove genre-agnostic capability
- Each world has different acceptance thresholds based on corpus characteristics

### **4. Performance Optimization**
- SentenceTransformers model loads once at startup (~30 seconds)
- FAISS search is sub-millisecond for real-time scoring
- Consider model caching for multiple instances

---

## 📞 Team Handoff Checklist

### **Files to Transfer**
- [ ] Complete `mythos_demo/` directory
- [ ] This deployment guide
- [ ] `requirements.txt` with exact versions
- [ ] Pre-built world indices in `worlds/` directory

### **Testing Sequence**
1. [ ] Start Island Scorer service (port 8000)
2. [ ] Verify health endpoint responds
3. [ ] Test scoring API with sample text
4. [ ] Update `working_demo.html` with remote server URL
5. [ ] Test all three worlds (greek_myth, fantasy_realm, vampire_cyberpunk)
6. [ ] Verify CORS allows browser access
7. [ ] Test all example buttons in demo

### **Success Metrics**
- [ ] Real-time scoring working (<1 second response)
- [ ] World switching functional
- [ ] Cross-genre validation demonstrates content-agnostic algorithm
- [ ] Demo accessible from external browsers

---

*This architecture enables your team to provide a professional, shareable demo while keeping the sophisticated AI/ML implementation details private and secure.*
