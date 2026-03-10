FROM python:3.10-slim

# Install system dependencies required for OpenCV and face recognition
RUN apt-get update --fix-missing && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement files first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create a pre-start script to download the model weights during build
# This avoids downloading weights on the first request in production
RUN python -c "from deepface import DeepFace; import os; os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'; print('Pre-downloading models...'); DeepFace.build_model('ArcFace'); print('Downloading RetinaFace...'); DeepFace.build_model('retinaface'); print('Models downloaded!')" || true

# Copy the rest of the application
COPY . .

# Expose port (Railway provides PORT environment variable)
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
