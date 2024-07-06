for i in 11 12 13 14 15 21 22 23 24 25 31 32 33 34 35 41 42 43 44 45
do
   echo "Starting Receiver on 192.168.254.${i}"
   ssh pi@192.168.254.${i} "/bin/bash /data/marquee/startReceiver.bash"
   echo "Done"
done 
