FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-rus \
    build-essential \
    cmake \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pybind11

COPY . .

RUN mkdir -p cpp_utils/build && \
    cd cpp_utils/build && \
    cmake -Dpybind11_DIR=$(python3 -c "import pybind11; print(pybind11.get_cmake_dir())") .. && \
    make && \
    cp cpp_iou*.so /app/

CMD ["python", "-m", "main"]