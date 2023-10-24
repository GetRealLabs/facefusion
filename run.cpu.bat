docker build . -f Dockerfile.cpu -t facefusion-cpu
docker run -it --rm ^
    -p 8080:7860 ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\facefusion\.insightface\:/root/.insightface/ ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\facefusion\.opennsfw2\:/root/.opennsfw2/ ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\facefusion\.assets\:/facefusion/.assets/ ^
    -v %HOMEDRIVE%%HOMEPATH%\ML\media\:/facefusion/media/ ^
    facefusion-cpu %*
   
REM --headless -s ./media/source.jpeg -t ./media/target.png -o ./media/output.png