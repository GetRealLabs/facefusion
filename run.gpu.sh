docker build . -f Dockerfile.gpu -t facefusion-gpu
docker run -it --rm \
    --gpus all \
    -p 8080:7860 \
    -v ~/ML/facefusion/.assets/:/facefusion/.assets/ \
    facefusion-gpu $1