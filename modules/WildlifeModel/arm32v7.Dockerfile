FROM resin/raspberrypi3-debian:stretch
# The balena base image for building apps on Raspberry Pi 3.

RUN echo "BUILD MODULE: Wildlifeclassifier"

# Enforces cross-compilation through Quemu
RUN [ "cross-build-start" ]

RUN apt-get update && apt-get install -y python3-pip libboost-python-dev

# Install dependencies
RUN apt-get update &&  apt-get install -y \
        python3 \
        python3-pip \
        build-essential \
        python3-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        zlib1g-dev \
        libjpeg-dev \
        libatlas-base-dev \
        wget

# Python dependencies
COPY /build/arm32v7-requirements.txt ./
RUN pip3 install --upgrade pip 
RUN pip3 install --upgrade setuptools
RUN pip3 install --index-url=https://www.piwheels.org/simple -r arm32v7-requirements.txt

# Add the application
ADD app /app

# Expose the port
EXPOSE 80

# Set the working directory
WORKDIR /app

# End cross building of ARM on x64 hardware, Remove this and the cross-build-start if building on ARM hardware.
RUN [ "cross-build-end" ]

# Run the flask server for the endpoints
CMD ["python3","app.py"]