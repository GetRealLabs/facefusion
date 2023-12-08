docker build . -f Dockerfile.cpu -t facefusion-cpu
docker run -it --rm \
    -p 8080:7860 \
    -v ~/ML/facefusion/.insightface/:/root/.insightface/ \
    -v ~/ML/facefusion/.opennsfw2/:/root/.opennsfw2/ \
    -v ~/ML/facefusion/.assets/:/facefusion/.assets/ \
    -v ~/ML/facefusion/root/:/root/ \
    -v ~/ML/media/:/facefusion/media/ \
    facefusion-cpu "$@"
   
# -s /facefusion/media/source.jpeg -t /facefusion/media/target.mp4 -o /facefusion/media/output.mp4
