docker build . -f Dockerfile.cuda -t facefusion-gpu
docker run -it --rm ^
    --gpus=all ^
    -p 8080:7860 ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\facefusion\.insightface\:/root/.insightface/ ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\facefusion\.opennsfw2\:/root/.opennsfw2/ ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\facefusion\.assets\:/facefusion/.assets/ ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\media\:/facefusion/media/ ^
    facefusion-gpu %*
   
REM --headless -s ./media/source.jpeg -t ./media/target.png -o ./media/output.png