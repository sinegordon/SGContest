FROM ubuntu:20.04
LABEL maintainer="zdv@mst-company.ru"
WORKDIR /app
RUN apt-get update -q
RUN apt-get -y -q install wget
RUN wget http://download.mono-project.com/repo/xamarin.gpg
RUN apt-get -y -q install gnupg
RUN apt-key add xamarin.gpg
RUN rm xamarin.gpg
RUN echo "deb http://download.mono-project.com/repo/debian stable-focal main" > /etc/apt/sources.list.d/mono-xamarin.list
RUN apt-get update -q
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get -qy install mono-complete
RUN apt-get update -q
RUN apt -y install build-essential
RUN apt-get -y install python3
RUN apt -y install python3-pip
COPY requirements.txt .
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
