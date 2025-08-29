# Forward Diffusion Project

## Frontend (React + Vite)
1. Navigate to the frontend folder:
   cd frontend
2. Install dependencies:
   npm install
3. Start the development server:
   npm run dev
4. Open the app in your browser: http://localhost:5173

---

## Backend (FastAPI + SQLAlchemy)
1. Navigate to the backend folder:
   cd backend
2. Install dependencies:
   pip install -r requirements.txt
3. Run the server:
   uvicorn app.main:app --reload

---

## 🗄️ Database & Migrations
- Make sure you have a MySQL database running (configured in `settings.DATABASE_URL`).
- Apply migrations if needed:
   alembic upgrade head
  (Run this inside the backend folder.)
---

## Docker (Optional)
You can also spin up the whole stack using Docker Compose:

   docker compose up --build

- Frontend → http://localhost:5173  
- Backend → http://localhost:8000  
- Database → MySQL running on port 3307

