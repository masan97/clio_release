#! /bin/bash

name_image=${1}

mkdir /home/$USER/tmp

sudo docker run -d -p 5000:5000 --restart always --name registry registry:2

sudo docker tag $name_image localhost:5000/$name_image
sudo docker push localhost:5000/$name_image

SINGULARITY_TMPDIR=/home/$USER/tmp SINGULARITY_NOHTTPS=true singularity build $name_image.simg docker://localhost:5000/$name_image
