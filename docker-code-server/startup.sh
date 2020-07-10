#DUPLO_CHANGE: START
echo "START********************* DOCKER RUN Firefox *********************START"
sudo docker ps
if [ $(sudo docker ps | grep firefox | wc -l) -gt 0 ]
then
    echo "**** Firefox is Running! "
else
    echo "**** Firefox is Not running!"
    sudo docker run -d --name firefox -v /docker/appdata/firefox:/config --network host  jlesage/firefox:latest
fi
#sudo docker rm -f firefox
#sudo docker run -d --name firefox -v /docker/appdata/firefox:/config --network host  jlesage/firefox:latest
sudo docker ps
echo "END********************** DOCKER RUN Firefox *********************END "
#DUPLO_CHANGE: END
