FROM python:3.12

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "frontend.py", "--server.port=8080", "--server.address=0.0.0.0"]