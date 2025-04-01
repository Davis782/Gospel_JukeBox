FROM python:3.11-slim

# Create the missing directory and set permissions
RUN mkdir -p /var/lib/apt/lists/partial && chmod -R 777 /var/lib/apt/lists

# Update and install the required packages
RUN apt-get update && apt-get install -y xvfb xauth

# Copy your requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code to the /app directory
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Run the application; note the path depends on your repository structure.
# If your Gospel_JukeBox.py is in the repository root (now in /app),
# use "Gospel_JukeBox.py" instead of "app/Gospel_JukeBox.py".
CMD ["python", "Gospel_JukeBox.py"]
