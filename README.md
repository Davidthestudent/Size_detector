# 👕 Size Detector


## 📌 Project Overview  
**Size Detector** is a FastAPI-based web service that predicts clothing sizes from uploaded images.  
It leverages **deep learning** for image understanding and returns both descriptive captions and predicted clothing sizes.  
Ideal for **e-commerce platforms, fashion retailers, and research projects**.  

---

## 🚀 Features  
- 📷 Upload and process images via REST API (FastAPI endpoints)  
- 🧠 Image captioning with HuggingFace **BLIP**  
- 📏 Clothing size prediction using **PyTorch** models  
- 📑 Interactive API docs with **Swagger** (`/docs`)  
- 🐳 Easy deployment with **Docker**  

---

## 🛠️ Tech Stack  
- **Python 3.13**  
- **FastAPI** – backend framework  
- **PyTorch** – deep learning & inference  
- **Transformers (HuggingFace)** – BLIP for image captioning  
- **Uvicorn** – ASGI server  
- **Docker** – containerization  

---

## ⚡ Installation & Run  

Clone the repository:  
```bash
git clone https://github.com/Davidthestudent/Size_detector.git
cd Size_detector
```

Install dependencies:  
```bash
pip install -r requirements.txt
```

Run the server:  
```bash
uvicorn service:app --reload
```

Access the API docs:  
```
http://127.0.0.1:8000/docs
```

---

## 📂 Project Structure  
```
Size_detector/
│── main.py          # Core model pipeline
│── service.py       # FastAPI endpoints
│── requirements.txt # Dependencies
│── Dockerfile       # Containerization setup
```

---

## 🔮 Roadmap / Possible Improvements  
- 🌐 Add a simple frontend for image upload  
- 📊 Store predictions & analytics  
- 🎯 Train a custom dataset for clothing-specific size detection  
- 🔗 Extend support to multimodal (text + image) inputs  

---

👨‍💻 Developed by **David Zunduev**  
📌 Repository: [github.com/Davidthestudent/Size_detector](https://github.com/Davidthestudent/Size_detector)
