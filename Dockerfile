# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install dependencies
RUN apt-get update && apt-get install -y \
    apt-utils \
    wget \
    curl \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    gnupg \
    mesa-vulkan-drivers \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 02 available
EXPOSE 02

# Define environment variable
ENV BOT_TOKEN=${BOT_TOKEN}
ENV DRIVER_PATH=${DRIVER_PATH}
ENV SERVER_LINK=${SERVER_LINK}
ENV APPLICATION_ID=${APPLICATION_ID}

# Run bot.py when the container launches
CMD ["python", "bot.py"]