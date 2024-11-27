FROM python:3.11.2

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip


RUN mkdir -p /app/images
RUN mkdir -p /app/applicant_data

COPY requirements.txt /app/
COPY *.py /app/
COPY ./images/* /app/images/

RUN pip3 install -r requirements.txt
