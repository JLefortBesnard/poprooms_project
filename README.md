# poprooms_project
Python project for extracting best appartment offers from rent.591.com.tw for the company https://pop-rooms.com/

Extract price, GPS coordinates of each appartment listed on the 591 webpages and compute distance from Taipei city center and each MRT station and return best price and best location (closest MRT station, closest distance from center).

Python 3.
Modules needed: urllib.request, bs4, math, re, pandas, time, numpy, datetime.
Make sure you downloaded the MRT_gps.txt as well and both the script and the txt file are in the same folder. When running the script on your terminal, you should be in that directory. You also need an internet connection.

More information: https://losangebleu.site/public/webpages/poprooms.php


IMPORTANT: Not all Taipei MRT stations are listed in the txt file here. You need to complete the job manually using Google maps and clicking on each missing MRT station to get their coordinates. 
