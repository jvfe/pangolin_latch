FROM 812206152185.dkr.ecr.us-west-2.amazonaws.com/latch-base:6839-main

RUN apt-get install -y curl

# Get miniconda
RUN curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh --output miniconda.sh
ENV CONDA_DIR /opt/conda
RUN bash miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Get Mamba
RUN conda install mamba -n base -c conda-forge

# Get pangolin and multiqc
RUN mamba install -y -c bioconda -c conda-forge -c defaults pangolin==4.1.2 multiqc

# RUN mamba create -y -n pango_env -c bioconda -c conda-forge -c defaults pangolin==4.1.2 multiqc
# ENV META_ENV $CONDA_DIR/envs/pango_env/bin

# Create symlink
# RUN ln -s $META_ENV/pangolin /root/pangolin
# RUN ln -s $META_ENV/multiqc /root/multiqc 


# STOP HERE:
# The following lines are needed to ensure your build environement works
# correctly with latch.
RUN python3 -m pip install --upgrade latch
COPY wf /root/wf
ARG tag
ENV FLYTE_INTERNAL_IMAGE $tag
WORKDIR /root
