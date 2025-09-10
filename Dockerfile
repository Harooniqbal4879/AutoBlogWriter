# AutoBlogWriter Dockerfile
# Build with: docker build -t autoblogwriter .
# Run with: docker run -p 8501:8501 --env-file .env autoblogwriter

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Entrypoint: run Streamlit app
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port", "8501"]
