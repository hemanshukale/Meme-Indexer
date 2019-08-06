# Meme-Indexer
Scans memes/images for text and names them according to the text found  

When you have 5k+ stored memes but almost none of them have a descriptive name and you spend minutes fnding just the perfect meme for the situation.. This script tries to solve the problem. 

The image is enhanced - contrast and sharpness wise using **PIL** then thresholded : made to pure black and white.  
**PyTesseract** is used for finding text in the image, **PyEnchant** is used to find the best match by counting the max valid words for a variety of thresholds.  
The converted text is then sanitized to a proper file name and spaces are replaced with underscores.

The original files are retained and a new folder is created in the given path with name as output_<timestamp>. 
All the images are copied on the folder and named as per text found in it.
If no text is found, the original name persists and 'NA_' of added before the name.  

**Script Inputs:**  
Enter **'p'** when the script is running to pause the script in case you need to use the computing resources in any other task.  
**'+'** and **'-'** are other accepted inputs and increase / decrease delay by 4ms respectively. 
Multiple inputs are accepted. ex. **'++++++'** will increase the delay by 24ms (4ms for each '+')
Press enter after every input.  

**Python modules used :**
os, pytesseract, sys, time, PIL, argparse, inspect, datetime, shutil, traceback, pathvalidate, threading

**Some stats :**  
Single Thread: I ran on ~2100 (~225MB) images with 7 threshold ranges to maximise chances of max text getting captured and it took around 140 mins for the whole run with a very low processor usage and around 5% were not converted due to improper image plane.  
Multi Thread : Same Dataset was ran with 4 Threads and total time taken was ~50 mins. However processor usage was >90% for majority of time. 

**Arguments:**  
Specify path with -p  
Disable use of  dictionary : -nd  
Indicate number of threads : -t
Sample run command : python Meme-Indexer.py -p '/home/memes/'

**Multithreading:**  
This update has multithreading enabled, use -t <number> to enable multithreading and specify number of threads. 
If ran without the argument, it will run with single thread.  
Caution : It uses processor extensively,  hence it is advisable to not to use > 3 threads unless your processor has sufficient cooling 

**Planned Updates**

Ability to identify if the text is at an angle and bringing it to proper angle for better processing.

