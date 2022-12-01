FROM ubuntu:bionic
LABEL maintainer="zdv@mst-company.ru"
WORKDIR /app
RUN apt-get update -q
RUN apt-get -y -q install wget
RUN wget http://download.mono-project.com/repo/xamarin.gpg
RUN apt-get -y -q install gnupg
RUN apt-key add xamarin.gpg
RUN rm xamarin.gpg
RUN echo "deb http://download.mono-project.com/repo/debian stable-bionic main" > /etc/apt/sources.list.d/mono-xamarin.list
RUN apt-get update -q
RUN apt-get -y -q install mono-complete
RUN apt-get install python3
RUN python3 -m pip install -r requirements.txt --no-cache-dir
COPY . .
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
STOPSIGNAL SIGINT
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:api"]

#FROM python:3.8-alpine
#LABEL maintainer="vla@mst-company.ru"
#WORKDIR /app
#COPY requirements.txt .
#RUN python3 -m pip install -r requirements.txt --no-cache-dir
#COPY . .
#EXPOSE 8000
#ENV PYTHONUNBUFFERED=1
#STOPSIGNAL SIGINT
#CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:api"]
