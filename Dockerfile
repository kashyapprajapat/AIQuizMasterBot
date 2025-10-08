FROM python:3.11-slim

WORKDIR /code

# Copy requirements file
COPY requirements.txt .

# Install all dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app
COPY ./telegram-bot ./telegram-bot
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run both services
CMD ["./start.sh"]