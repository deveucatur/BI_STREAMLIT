FROM python:3.9-slim

LABEL description="Bi Streamlit Eucatur"
LABEL maintainer="Eulabs Tecnologia"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN git clone https://<<token>>git@github.com:deveucatur/BI_STREAMLIT.git .

RUN pip3 install -r requirements.txt

EXPOSE 8506

HEALTHCHECK CMD curl --fail http://localhost:8506/_stcore/health

ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8506", "--server.address=0.0.0.0"]