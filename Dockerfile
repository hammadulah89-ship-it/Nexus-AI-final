FROM python:3.11-slim

WORKDIR /app

# Install runtime libraries for OpenCV & imaging
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Hugging Face Spaces port is 7860
ENV PORT=7860
ENV HOST=0.0.0.0
EXPOSE 7860

# Run FastAPI with uvicorn on port 7860
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
