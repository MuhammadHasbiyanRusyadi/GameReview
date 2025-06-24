# Gunakan official Python image sebagai base image
FROM python:3.9-slim-buster

# Set working directory di dalam container
WORKDIR /app

# Copy requirement.txt ke working directory
# Pastikan nama file adalah 'requirement.txt' (tunggal)
COPY requirement.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Copy semua file dari folder app lokal (termasuk app.py, static, templates, .env) ke working directory di container
COPY . .

# Expose port yang digunakan aplikasi Flask (default 5000)
EXPOSE 5000

# Command untuk menjalankan aplikasi
CMD ["python", "app.py"]
