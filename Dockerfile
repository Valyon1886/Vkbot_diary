FROM python:3.11.10-slim

# copy bot files and its requirements
WORKDIR /VkBotDiary/
ADD *.py /VkBotDiary/
ADD requirements.txt /VkBotDiary/

# install requirements
RUN pip install -r requirements.txt

# install ffmpeg and tzdata
RUN apt-get update
RUN apt-get -y install ffmpeg && apt-get install tzdata -y

# setup time zone
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Add docker-compose-wait tool
ENV WAIT_VERSION=2.12.1
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait ./wait-script
RUN chmod 775 ./wait-script