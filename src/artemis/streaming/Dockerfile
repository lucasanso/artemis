FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# --no-cache-dir reduces image size by not storing the download cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

