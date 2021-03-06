#!/bin/bash

arma_version=$1
boost_version=$2
gcc_version=$3

gcc_version_major=`echo ${gcc_version/gcc-} | sed 's/^\([0-9]\).*/\1/'`;

cat > Dockerfile << EOF
# Using debian's latest image as base-image plus mlpack prereqs.
FROM mlpack-docker-base:latest

# Installing gcc from source.  On newer gcc versions than the system gcc, we
# have to move all the libraries and bootstrap.
RUN wget --no-check-certificate \
   https://ftp.gnu.org/gnu/gcc/$gcc_version/$gcc_version.tar.gz && \
   tar xvzf $gcc_version.tar.gz && \
   rm -f $gcc_version.tar.gz && \
   cd $gcc_version && \
   ./contrib/download_prerequisites && \
   mkdir objdir && \
   cd objdir && \
   if [ $gcc_version_major -gt 6 ]; then \
     ../configure --prefix=/usr --enable-languages=c,c++,fortran \
        --disable-multilib --enable-bootstrap; \
   else \
     ../configure --prefix=/usr --enable-languages=c,c++,fortran \
       --disable-multilib --disable-bootstrap; \
   fi && \
   make -j32 && \
   make install && \
   if [ $gcc_version_major -gt 6 ]; then \
     mv /usr/lib64/* /usr/lib/x86_64-linux-gnu/; \
   fi && \
   cd ../../ && \
   rm -rf $gcc_version

# Installing boost from source
RUN wget --no-check-certificate \
      "http://masterblaster.mlpack.org:5005/$boost_version.tar.gz" && \
    tar xvzf $boost_version.tar.gz && \
    rm -f $boost_version.tar.gz && \
    cd $boost_version && \
    ./bootstrap.sh --prefix=/usr/ \
        -with-libraries=math,program_options,serialization,test && \
    ./bjam install -j32 && \
    cd ../ && \
    rm -rf $boost_version

# Installing armadillo via source-code.
RUN wget --no-check-certificate \
    http://masterblaster.mlpack.org:5005/$arma_version.tar.gz && \
    tar xvzf $arma_version.tar.gz && \
    rm -f $arma_version.tar.gz && \
    cd $arma_version && \
    cmake -DINSTALL_LIB_DIR=/usr/lib . && \
    make -j32 && \
    make install && \
    cd .. && \
    rm -rf $arma_version
EOF

cat >> Dockerfile << 'EOF'
# Creating a non-root user.
RUN adduser --system --disabled-password --disabled-login \
   --shell /bin/sh mlpack

# Hardening the containers by unsetting all SUID tags
RUN for i in `find / -perm 6000 -type f`; do chmod a-s $i; done

# Changing work directory again.
WORKDIR /home/mlpack
USER mlpack
EOF
