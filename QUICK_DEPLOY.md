# MythOS Remote Deployment - Quick Start Checklist

## 🚀 Immediate Deployment Steps

### **1. Essential Files to Upload**
```bash
# Copy these directories to remote server:
mythos_demo/
├── services/island_scorer/     # Core API service
├── corpus/                     # Reference text chunks  
├── worlds/                     # Pre-built FAISS indices (CRITICAL!)
├── requirements.txt            # Python dependencies
└── working_demo.html           # Client demo
```

### **2. Server Setup Commands**
```bash
# On remote server:
cd /opt/mythos
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Island Scorer (main service)
python -m services.island_scorer.app
# Should show: "Application startup complete" on port 8000
```

### **3. Update Client Demo**
```javascript
// In working_demo.html line ~414, change:
this.islandScorerUrl = 'http://YOUR-REMOTE-SERVER-IP:8000';
```

### **4. Test Endpoints**
```bash
# Health check
curl http://YOUR-SERVER:8000/health

# Test scoring
curl -X POST http://YOUR-SERVER:8000/score \
  -H "Content-Type: application/json" \
  -d '{"world_id": "greek_myth", "text": "Zeus ruled Olympus"}'
```

### **5. Serve Demo HTML**
```bash
# Simple Python server
python -m http.server 8080

# Demo URL: http://YOUR-SERVER:8080/working_demo.html
```

## 🎯 Success Validation

- [ ] Island Scorer starts without errors
- [ ] Health endpoint returns {"status": "healthy"}
- [ ] All 3 worlds load (greek_myth, fantasy_realm, vampire_cyberpunk)
- [ ] Demo connects (green "Island Scorer Connected" status)
- [ ] Real-time scoring works (<1 second response)
- [ ] World switching changes chunk counts correctly
- [ ] Cross-genre examples show different scores per world

## 🔧 Production Optimizations

### **Process Management**
```bash
# Use screen/tmux for persistent service
screen -S mythos
python -m services.island_scorer.app
# Ctrl+A, D to detach

# Or use systemd (see DEPLOYMENT_GUIDE.md)
```

### **Firewall/Security**
```bash
# Open required ports
ufw allow 8000  # Island Scorer API
ufw allow 8080  # Demo hosting (if using Python server)
```

### **Performance Notes**
- First startup: ~30 seconds (loading transformer model)
- Memory usage: ~4GB (model + embeddings)
- Response time: <500ms per scoring request
- FAISS indices: Pre-built, no rebuild needed

## 🌐 Sharing Strategy

**For Demo Purposes:**
- Share: `http://YOUR-SERVER-IP:8080/working_demo.html`
- Users see: Live worldliness meter with 3 genre worlds
- Hidden: All AI/ML implementation details

**Key Demo Features:**
- Real-time scoring as user types
- World selector (Greek Mythology, Fantasy Realm, Vampire Cyberpunk)  
- 11 test examples across 7 genres
- Reference chunk viewer
- Live meter with visual feedback

## ⚡ Quick Troubleshooting

**Service Won't Start:**
- Check Python version: `python --version` (need 3.11+)
- Check dependencies: `pip list | grep fastapi`
- Check ports: `netstat -tulpn | grep 8000`

**Demo Won't Connect:**
- Verify CORS enabled (should be by default)
- Check firewall: `ufw status`
- Test direct API: `curl http://localhost:8000/health`

**Performance Issues:**
- Check memory: `free -h` (need 4GB+ free)
- Check CPU: `top` (transformer model is CPU intensive)
- Restart service if needed

---

*This gets your team up and running with a shareable MythOS demo in ~15 minutes!*
