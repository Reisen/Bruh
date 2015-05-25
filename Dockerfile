FROM dock0/arch

VOLUME ["/config", "/data"]
EXPOSE 22 9001 9890 9891

RUN echo 'Server = http://mirrors.acm.wpi.edu/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
RUN pacman --noconfirm -Sy ghc cabal-install pkg-config zeromq python python-virtualenv supervisor redis make
ADD . /bruh
RUN /bruh/docker/bootstrap.sh

CMD /bruh/docker/run.sh
