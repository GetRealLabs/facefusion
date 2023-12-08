docker build . -f Dockerfile.cuda -t facefusion-cuda
docker run -it --rm \
    --gpus all \
    -p 8080:7860 \
    -v ~/ML/facefusion/.insightface/:/root/.insightface/ \
    -v ~/ML/facefusion/.opennsfw2/:/root/.opennsfw2/ \
    -v ~/ML/facefusion/.assets/:/facefusion/.assets/ \
    -v ~/ML/facefusion/root/:/root/ \
    -v ~/ML/media/:/facefusion/media/ \
    facefusion-cuda "$@"

# -s /facefusion/media/source.jpeg -t /facefusion/media/target.mp4 -o /facefusion/media/output.mp4
