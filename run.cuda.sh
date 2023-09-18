docker build . -f Dockerfile.cuda -t facefusion-cuda
docker run -it --rm \
    --gpus all \
    -p 8080:7860 \
    -v ~/ML/facefusion/.assets/:/facefusion/.assets/ \
    facefusion-cuda $1