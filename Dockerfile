FROM python:3.12-alpine

RUN addgroup --system gdwrapper && adduser --system --ingroup gdwrapper --disabled-password gdwrapper

USER gdwrapper

RUN cd ~ && mkdir app

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./hello_world .

CMD [ "python3", "main.py" ]