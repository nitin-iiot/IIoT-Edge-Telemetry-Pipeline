# 1. Base Image: We pull a microscopic version of Linux with Python 3.9 pre-installed.
FROM python:3.9-slim

# 2. Workspace: We create a folder inside the container called /app and move inside it.
WORKDIR /app

# 3. Tool List: We copy the requirements file from your laptop into the container.
COPY requirements.txt .

# 4. Installation: We tell the container's OS to install the MQTT library.
RUN pip install --no-cache-dir -r requirements.txt

# 5. The Payload: We copy your updated Python script into the container.
COPY cnc_sensor.py .

# 6. Execution: The exact command the container runs the second it boots.
# The "-u" flag forces Python to print logs to the terminal immediately, bypassing the buffer.
CMD ["python", "-u", "cnc_sensor.py"]

