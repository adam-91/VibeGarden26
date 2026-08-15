FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=xcb

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libopengl0 \
    libglib2.0-0 \
    libfontconfig1 \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxkbcommon-x11-0 \
    libegl1 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
