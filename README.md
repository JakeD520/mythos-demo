# 🏛️ MythOS Live Worldliness Meter - Demo

A real-time, content-agnostic worldliness scoring system that validates writing consistency against any genre corpus using semantic similarity and machine learning.

![MythOS Demo](https://img.shields.io/badge/Status-Live%20Demo-brightgreen) 
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![AI/ML](https://img.shields.io/badge/AI-SentenceTransformers-orange)

## 🎯 **What This Demonstrates**

**MythOS proves that worldliness scoring is content-agnostic** - the same algorithm adapts to any genre based purely on the reference corpus, with no hardcoded domain knowledge.

### **Live Demo Features**
- ⚡ **Real-time scoring** as you type (sub-second response)
- 🌍 **Multi-world support** with genre switching
- 📊 **Visual feedback** with live meter and status indicators  
- 🧪 **11 test examples** across 7 different genres
- 📚 **Reference chunk viewer** showing algorithm transparency

### **Proof of Content-Agnostic Algorithm**
- **Greek Mythology World** → Scores mythology content high, rejects sci-fi
- **Fantasy Realm World** → Scores fantasy content high, rejects modern romance  
- **Vampire Cyberpunk World** → Scores cyber-vampire content high, rejects classical vampires

*Same algorithm, completely different standards based on corpus!*

## 🚀 **Quick Start**

### **⚡ One-Click Demo (Easiest)**
```bash
# Windows
start_demo.bat

# Linux/Mac  
./start_demo.sh

# Cross-platform Python script
python start_demo.py
```

**That's it!** The script will:
- ✅ Set up virtual environment automatically
- ✅ Install all dependencies  
- ✅ Start the Island Scorer service
- ✅ Auto-open the demo in your browser (after 35 seconds)

### **Manual Setup (If needed)**
```bash
# Clone and setup
git clone https://github.com/JakeD520/mythos-demo.git
cd mythos-demo
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the Island Scorer service
python -m services.island_scorer.app

# Open working_demo.html in your browser
```

### **Remote Deployment**
See [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for 15-minute server setup or [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for full production deployment.

## 🏗️ **Architecture**

### **Core Technology Stack**
- **Backend**: FastAPI with Python 3.11+
- **AI/ML**: SentenceTransformers (all-MiniLM-L6-v2) + FAISS HNSW indexing
- **Frontend**: Vanilla HTML/CSS/JavaScript with CORS-enabled API calls
- **Real-time**: HTTP polling (WebSocket-less for simplicity)

### **Service Architecture**
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Island Scorer     │    │    Prose Store      │    │      Editor         │
│   Port: 8000        │    │    Port: 8001       │    │    Port: 8002       │
│   ✅ CORE SERVICE   │    │   🔧 Optional       │    │   🔧 Optional       │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
          │
          └─── HTTP API ────┐
                            │
                    ┌─────────────────────┐
                    │  Client HTML Demo   │
                    │  working_demo.html  │
                    └─────────────────────┘
```

## 🎮 **How to Test the Content-Agnostic Algorithm**

1. **Start with Greek Mythology world**
   - Try: "Zeus ruled from Mount Olympus" → Should ACCEPT
   - Try: "Spaceships landed on Mars" → Should REJECT

2. **Switch to Fantasy Realm world** 
   - Try: "Dragons hoarded gold" → Should ACCEPT
   - Try: "Coffee shop romance" → Should REJECT

3. **Switch to Vampire Cyberpunk world**
   - Try: "Neural implants glowed red" → Should ACCEPT  
   - Try: "Classical castle vampire" → Should REJECT

**Key Insight**: Same vampire content scores differently in Fantasy vs Cyberpunk worlds!

## 📁 **Project Structure**

```
mythos_demo/
├── services/
│   └── island_scorer/          # 🎯 Core API service (Port 8000)
│       ├── app.py             # FastAPI application
│       ├── build.py           # World building logic  
│       ├── score.py           # Scoring algorithm
│       └── models.py          # Pydantic data models
├── corpus/                    # 📚 Reference text chunks
│   ├── greek_myth/           # 13 mythology chunks
│   ├── fantasy_realm/        # 9 fantasy chunks
│   └── vampire_cyberpunk/    # 9 cyberpunk chunks  
├── worlds/                   # 🧠 Pre-built FAISS indices
│   ├── greek_myth.index      # 384-dim embeddings
│   ├── fantasy_realm.index
│   └── vampire_cyberpunk.index
├── working_demo.html         # 🎪 Interactive demo interface
├── requirements.txt          # 📦 Python dependencies
├── DEPLOYMENT_GUIDE.md       # 🚀 Full deployment docs
└── QUICK_DEPLOY.md          # ⚡ 15-minute setup guide
```

## 🔬 **Algorithm Deep Dive**

### **Content-Agnostic Scoring Process**
1. **Input text** → SentenceTransformers embedding (384-dimensional)
2. **FAISS search** → Find nearest reference chunks in vector space
3. **Distance calculation** → Compute semantic similarity scores
4. **Adaptive thresholds** → Apply world-specific accept/review/reject thresholds
5. **Real-time response** → Return score + status + reference chunks

### **Why It's Content-Agnostic**
- ✅ **No hardcoded keywords** - Pure semantic similarity
- ✅ **No genre preferences** - Algorithm identical across all worlds
- ✅ **Corpus-driven standards** - Thresholds computed from reference content
- ✅ **Contextual adaptation** - Same text scores differently per world

## 🎯 **Key Features Demonstrated**

### **Real-Time Validation**
- Sub-second response times with transformer models
- Live visual feedback with animated meter
- Debounced input for smooth user experience

### **Multi-Genre Support**  
- Three distinct worlds with different content types
- Automatic threshold calculation per corpus
- Cross-genre testing validates content-agnostic claims

### **Transparency & Explainability**
- Shows nearest reference chunks that influenced score
- Distance scores for debugging and understanding
- Visual indicators for accept/review/reject decisions

## 🚀 **Deployment Options**

### **1. Development/Testing**
- Local Python server on localhost
- File-based HTML demo 
- Perfect for development and local testing

### **2. Remote Demo Hosting**
- Server-hosted API with static HTML frontend
- CORS-enabled for cross-origin requests
- Shareable URLs for stakeholder demos

### **3. Production Deployment**
- Dockerized services with load balancing
- CDN for static assets
- SSL/HTTPS with custom domains

## 📊 **Performance Metrics**

- **Model Loading**: ~30 seconds (one-time startup cost)
- **Scoring Response**: <500ms average 
- **Memory Usage**: ~4GB (transformer model + embeddings)
- **Concurrent Users**: 50+ (with proper hardware)
- **World Switching**: Instant (pre-computed indices)

## 🤝 **Contributing**

This is a proof-of-concept demonstration. For production use cases:

1. **Extend corpus size** - Add more reference chunks per world
2. **Add new worlds** - Create corpuses for additional genres
3. **Optimize performance** - GPU acceleration, model quantization
4. **Enhanced UI** - Additional visualizations and features

## 📜 **License**

This project is a demonstration of content-agnostic worldliness scoring technology.

---

## 🎪 **Try the Live Demo**

**The key insight**: Load the same text in different worlds and watch how the algorithm adapts its standards based purely on the reference corpus. This proves MythOS creates truly flexible, content-agnostic writing validation systems.

*Built with ❤️ to demonstrate the future of adaptive content validation*
