FROM ubuntu:16.04

# production build
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
RUN apt-get update
RUN apt-get install -y python-software-properties software-properties-common
RUN add-apt-repository -y ppa:ubuntu-toolchain-r/test
RUN apt-get update
RUN apt-get install -y g++-7
RUN apt-get install -y gcc-7
RUN add-apt-repository -y ppa:webupd8team/java
RUN apt-get update
RUN apt-get install -y build-essential time nasm unzip
RUN apt-get install -y default-jre
RUN apt-get install -y default-jdk
RUN rm -rf /var/lib/apt/lists/*

CMD ["bash"]
