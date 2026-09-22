# 1. Base image: a small Linux with Python 3.9.
FROM python:3.9-slim

# 2. Workspace inside the container.
WORKDIR /app

# 3. Copy the dependency list.
COPY requirements.txt .

# 4. Install the Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the gateway script into the container.
COPY edge_gateway.py .

# 6. Run it. "-u" makes Python flush logs immediately (no buffering).
CMD ["python", "-u", "edge_gateway.py"]
