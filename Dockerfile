FROM ubuntu:latest


ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y python3 python3-pip llvm clang && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /app

WORKDIR /app

COPY main.py /app/main.py
COPY rinha.py /app/rinha.py

COPY files /var/rinha

RUN pip3 install llvmlite

CMD ["python3", "main.py"]
