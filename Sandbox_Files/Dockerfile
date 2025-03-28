FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY Gospel_JukeBox.py .

# Create necessary directories
RUN mkdir -p mp3_files pictures data/songs

# Copy essential data files
COPY mp3_files/ mp3_files/
COPY pictures/ pictures/
COPY data/ data/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]