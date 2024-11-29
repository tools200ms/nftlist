FROM ubuntu:latest
LABEL authors="barney"

ENTRYPOINT ["top", "-b"]