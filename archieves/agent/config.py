import os

ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = os.getenv('SMTP_PORT', 465)
SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'your-email@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your-email-password')
LLAMA3_API_URL = os.getenv('LLAMA3_API_URL', 'http://dlyog04:8893/llama3')
