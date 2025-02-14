# Po Vision dockerfile

FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# 複製 requirements.txt 並安裝 Python 套件
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製其餘代碼
COPY . .

# 設定環境變數
ENV FLASK_APP=OCR_app.py 
ENV FLASK_ENV=production


# 使用 Gunicorn 作為生產伺服器
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3001", "OCR_app:app"]
