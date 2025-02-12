FROM python:3.9-slim
WORKDIR /src

# Install CA certificates and update the system
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host files.pythonhosted.org -r requirements.txt

# Copy the application code
COPY . .

# Run the application
CMD ["python", "app.py"]