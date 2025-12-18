FROM ubuntu:latest

RUN apt-get update && apt upgrade -y && apt install python3-pip python3-venv -y && apt autoremove -y
COPY . /tpp
WORKDIR /tpp
RUN python3 -m venv .venv
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD [".venv/bin/python", "-m", "swagger_server"]