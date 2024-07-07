for i in 11 12 13 14 15 21 22 23 24 25 31 32 33 34 35 41 42 43 44 45
do
   echo "Starting Receiver on 10.10.10.${i}"
   ssh pi@10.10.10.${i} "/bin/bash /home/pi/pi-code/marquee/startReceiver.bash"
   echo "Done"
done 
