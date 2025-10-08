FROM python:3.11-slim

WORKDIR /code

# Copy requirements files
COPY requirements.txt .
COPY telegram-bot/requirements.txt telegram-bot-requirements.txt

# Install all dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r telegram-bot-requirements.txt

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