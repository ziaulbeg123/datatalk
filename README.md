# DataTalk 🗣️📊
> Ask your CSV data anything. In plain English.

---

## 🗂️ Project Structure

```
datatalk/
├── frontend/
│   └── index.html          ← Landing page (deploy to Vercel/Netlify)
├── backend/
│   ├── main.py             ← FastAPI app (deploy to Railway)
│   └── requirements.txt
├── railway.toml            ← Railway deployment config
└── README.md
```

---

## ⚙️ Local Setup (Day 1)

### Step 1 — Clone & setup

```bash
# Create folder
mkdir datatalk && cd datatalk

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Step 2 — Add your API key

Create a `.env` file in `/backend`:

```
OPENAI_API_KEY=sk-your-key-here
```

Get key from: https://platform.openai.com/api-keys
Cost: ~$0.001 per question (basically free to start)

### Step 3 — Run backend locally

```bash
cd backend
uvicorn main:app --reload
```

Open: http://localhost:8000
API docs: http://localhost:8000/docs  ← Very useful!

### Step 4 — Test with curl

```bash
# Upload a CSV
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_data.csv"

# Returns: {"session_id": "abc-123", ...}

# Ask a question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc-123", "question": "Which product had highest sales?"}'
```

---

## 🚀 Deployment (Day 2-3)

### Backend → Railway.app (FREE)

1. Go to https://railway.app → Sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your repo → Railway auto-detects Python
4. Add environment variable:
   - Key: `OPENAI_API_KEY`
   - Value: your key
5. Deploy! Railway gives you a URL like: `https://datatalk-backend.up.railway.app`

### Frontend → Vercel (FREE)

1. Go to https://vercel.com → Sign up with GitHub
2. Import your repo → Select `frontend` folder
3. Deploy! Vercel gives you: `https://datatalk.vercel.app`
4. Update the API URL in your frontend JS to point to your Railway backend URL

---

## 💰 Cost Breakdown (Starting Out)

| Service | Cost |
|---------|------|
| Railway (backend) | Free up to $5/month usage |
| Vercel (frontend) | Free forever |
| OpenAI API | ~$0.001 per question |
| Domain (optional) | ~$10/year |
| **Total to launch** | **$0** |

---

## 📈 What to Build Next (Week 2-3)

- [ ] User authentication (use Supabase — free tier)
- [ ] Stripe payments ($9/month plan)
- [ ] Dashboard UI (React app)
- [ ] Chart rendering (Chart.js in frontend)
- [ ] Email notifications
- [ ] Usage limits per plan

---

## 🎯 First Customer Checklist

- [ ] Backend deployed on Railway
- [ ] Landing page live on Vercel
- [ ] Custom domain bought (datatalk.app or similar)
- [ ] 5 beta users signed up (family/friends/LinkedIn)
- [ ] First paying customer within 30 days

---

## 📞 Need Help?

API docs auto-generated at: `your-backend-url/docs`
All endpoints are tested and documented there.
