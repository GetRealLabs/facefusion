docker build . -f Dockerfile.cpu -t facefusion-cpu
docker run -it --rm \
    -p 8080:7860 \
    -v ~/ML/facefusion/.assets/:/facefusion/.assets/ \
    facefusion-cpu $1
   
# -s ./media/source.jpeg -t ./media/target.png -o ./media/output.png