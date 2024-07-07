#!/bin/bash

c1="[fg:red]"
c2="[fg:white]"
msg="Worldpay - Leaders In Modern Money - Innovating In Secure Analytics"

c1="[fg:aqua]"
c2="[fg:orangered]"
msg="CONFLUENT - KAFKA                         "

c1="[fg:blue]"
c2="[fg:white]"
msg="Data Management & Warehousing"

colour="${c1}"

grep -o . <<<  `echo ${msg}` | while read letter
do
   if [ "${letter}" == '' ]
   then
      echo -n ' ' 
   else 
      if [ "${colour}" == "${c1}" ]
      then
         colour="${c2}"
      else   
         colour="${c1}"
      fi
      echo -n "${colour}${letter}"
   fi 
done
echo
