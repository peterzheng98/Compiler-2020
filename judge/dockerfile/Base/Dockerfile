FROM swift:5.1.3-bionic

RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
RUN apt-get update
RUN apt-get install -y python3-software-properties software-properties-common
RUN echo 'deb http://ppa.launchpad.net/ubuntu-toolchain-r/test/ubuntu bionic main' >> /etc/apt/sources.list
RUN echo 'deb-src http://ppa.launchpad.net/ubuntu-toolchain-r/test/ubuntu bionic main' >> /etc/apt/sources.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 60C317803A41BA51845E371A1E9377A2BA9EF27F

RUN apt-get update
RUN apt-get install -y g++-7
RUN apt-get install -y gcc-7
RUN echo add-apt-repository -y ppa:webupd8team/java
RUN apt-get update
RUN apt-get install -y build-essential time nasm unzip
RUN apt-get install -y default-jdk
RUN javac -version
RUN apt-get install -y default-jre
RUN echo clang --version
RUN echo apt-get install -y clang
RUN echo add-apt-repository -y ppa:deadsnakes/ppa
RUN echo 'deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu bionic main' >> /etc/apt/sources.list
RUN echo 'deb-src http://ppa.launchpad.net/deadsnakes/ppa/ubuntu bionic main' >> /etc/apt/sources.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776
RUN apt-get update
RUN apt-get install -y python3.7
RUN apt-get install -y vim
RUN rm -rf /var/lib/apt/lists/*
COPY java/* /ulib/java/
COPY kotlin/* /ulib/kotlin/
RUN chmod 777 /ulib

CMD ["bash"]