from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os

app = FastAPI()

# Cross-Origin Resource Sharing (CORS) သတ်မှတ်ခြင်း
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB ချိတ်ဆက်ခြင်း (Vercel Environment Variable သို့မဟုတ် ဤနေရာတွင် တိုက်ရိုက်ထည့်ပါ)
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://dxstr47_db_user:xDs62AdrRbDHhgFH@cluster0.fso9l3s.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client["teletv_db"]
movies_collection = db["movies"]

@app.get("/api/movies")
def get_all_movies():
    """ ရရှိနိုင်သော Movie အားလုံးကို Frontend သို့ ပို့ပေးရန် """
    movies = list(movies_collection.find({}, {"_id": 0}))
    return movies

@app.get("/api/movies/{slug}")
def get_movie_detail(slug: str):
    """ Slug ကို အခြေခံပြီး Movie တစ်ကားချင်းစီ၏ အသေးစိတ်ကို ရှာပေးရန် """
    movie = movies_collection.find_one({"slug": slug}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
