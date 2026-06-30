Build :
```bash
docker build -t clio-image .
```
Run and mount current directory inside container :
```bash
docker  run  -v $(pwd):$(pwd) -w $(pwd) -i -t  clio-image /bin/bash
```
Convert to singularity:
```bash
bash convert_to_singularity.bash clio-image
```


