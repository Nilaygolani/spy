# 1. Base Python image python engine ke liye
FROM python:3.10-slim

# 2. Linux ke system packages aur Virtual Display (Xvfb) install karne ke liye
RUN apt-get update && apt-get install -y \
    xvfb \
    xserver-xorg \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxtst-dev \
    python3-tk \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Working directory set karein
WORKDIR /app

# 4. Requirements file copy aur install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Saara project code container me copy karein
COPY . .

# 6. Render ka port environment variable use karne ke liye
EXPOSE 10000

# 7. Xvfb (Virtual Display) ko background me start karke Gunicorn chalane ki command
CMD xvfb-run --server-args="-screen 0 1024x768x24" gunicorn --bind 0.0.0.0:10000 app:app
