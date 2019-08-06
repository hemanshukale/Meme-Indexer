import os, sys, time
from PIL import Image, ImageEnhance
import argparse, inspect, datetime, shutil, traceback
from pathvalidate import sanitize_filepath
from threading import Thread

max_path_len = 254 # Some system may have a limit on path length, Enter the limit here and such cases will be truncated till this length
p3 = sys.version_info > (2,8)
kill = False
pause = False
delay = 0

def ins():
    return inspect.getframeinfo(inspect.stack()[1][0]).lineno # For debugging, print line number which called this function

def Sort(lis, ind):
    return sorted(lis, key=lambda x: x[ind]) # Lambda function for sorting the given list by a custom index

def constrain(val, i,j): # Constraining Function
    if val < i: return i
    if val > j: return j
    return val

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path",required=False, help='Give path name' ) # path to the memes folder
parser.add_argument("-t", "--threads",required=False, help='Number of Threads ' ) # path to the memes folder
parser.add_argument("-nd", "--npdict",required=False, action="store_true", dest='nodict', help='Disable use of dictionary ' )
# parser.add_argument("-f", "--filter",required=False,nargs='*', help='Filter' )
# parser.add_argument("-ef", "--excludefilter",required=False, nargs='*', help='Exclusion filter' )

cmd_args  = parser.parse_args()
print(ins(), cmd_args)

if not cmd_args.nodict:
    print('Using dictionary')
    import enchant # For dictionary
    d = enchant.Dict("en_US")

path = cmd_args.path if cmd_args.path != None else os.getcwd() # use current working directory if no path given
print(ins(),'Using path :')

if not os.path.isdir(path): # Check if path valid
    print('invalid path\nExiting')
    sys.exit(1)

if cmd_args.threads == None :
    num_threads = 1 # Default Threads to 1 if multithreading option not provided
else :
    try : num_threads = int(cmd_args.threads)
    except : print('Thread count value NaN'); os._exit(1)
    if num_threads < 1 : print('Improper Thread count value '); os._exit(1)

err_str = ''
op_folder='output_' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') # Output Folder name with timestamp
thresh = [240, 220, 200, 150, 100, 50, 25]  # List of thresholds for converting to pure black and white

lis = os.listdir(path)
op_path = os.path.join(path,op_folder)
print('Output path = ', op_path)
os.mkdir(op_path) # Create output folder
print('Created Dir')
# lis_p = map(lambda x:os.path.join(path,x),lis)
if len(op_path) > max_path_len-8: # if the output folder path is already too long, no sense in continuing
    print('Too long path length')
    sys.exit(1)
done_count, err_count, eligible_count, na_count = 0,0,0,0

class Index(Thread):
    sub_lis = None
    num = None
    pyt = None
    def __init__(self, sub_lis, num):
        self.sub_lis = sub_lis
        self.num = num
        import pytesseract as pyter
        self.pyt = pyter # Each instance has own import statement for better multithreading
        Thread.__init__(self)

    def run(self):
        global max_path_len, cmd_args, path, err_str, op_folder, pause, delay
        global thresh, done_count, err_count, eligible_count, na_count, kill
        print(ins(), self.num, len(self.sub_lis))
        # time.sleep(2)
        print(ins(), self.num, len(self.sub_lis))
        # sys.exit(0)
        op_temp_path = os.path.join(op_path, 'temp_T'+str(self.num))
        os.mkdir(op_temp_path)  # Make 1 new temp path in the output folder per 1 thread
        os.chdir(op_temp_path)
        for i in self.sub_lis:
            try:
                time.sleep(delay)
                if kill :
                    os._exit(0)
                while pause: # Option to pause if it's taking too much processing power and you want to do something else
                    time.sleep(0.5)
                ext = i.split('.')[-1] # get extension of the file name
                if ext.lower() not in ['png', 'jpg', 'jpeg', 'bmp']:
                    print('Skipping',i )
                    continue
                j = os.path.join(path,i)
                new_path = os.path.join(op_temp_path, i)
                shutil.copy(j, new_path) # Copy the file in the new path (Temp Thread folder in the output folder)
                eligible_count += 1
                img_o = Image.open(new_path) # Open image
                contrast = ImageEnhance.Contrast(img_o)
                img = contrast.enhance(1.2) # Enhance contrast
                sharp = ImageEnhance.Sharpness(img)
                img = sharp.enhance(1.2) # Enhance Sharpness
                words = []
                for thres in thresh: # Loop over the thresholds
                    fn = lambda x : 255 if x > thres else 0 # Apply thresholding
                    img_t = img.convert('L').point(fn, mode='1'); # Convert into Pure Black & White
                    text = self.pyt.image_to_string(img_t, lang='eng') # Convert image to text
                    dcount = 0
                    if text == '': text = 'NA_'+i; dcount -= 255 # Concat 'NA_' at beginning of original file name if no text found
                    text = sanitize_filepath(text) # Remove Characters invalid for storing file name
                    text = text.replace('/', '').replace(' ', '_') # Remove slashes and replace spaces with underscores in file name
                    text = '_'.join([t for t in text.split('_') if t]) # Conver multiple consecutive <___> into one <_>
                    for w in text.split('_'): # Get one word
                        if w == '': continue
                        if not cmd_args.nodict: # Check if dictionary to be used
                            if d.check(w.lower()): dcount +=1 # Check if the word is valid
                            # d.suggest(w)
                        else: dcount +=1; #print(w);
                    words.append((thres, text, dcount))
                    print('T'+str(self.num), 'Thresh:', thres, ';', dcount,  text )
                words = Sort(words,2)
                text = words[-1][1] # Take the case where max valid words were found
                ext = '.' + ext
                if text == 'NA_' + i : na_count += 1; op_file = text
                else : op_file = text + ext
                op_file_path = os.path.join(op_path, op_file)
                diff = len(op_file_path+ext) - max_path_len # Check if path length > max Allowed
                # print(ins(), diff)
                if diff  > 0:
                    # op_file_path = op_file_path[:251]
                    op_file = op_file[:-diff-len(ext)] + ext # Trimming the file name to decrease path name
                    print(ins(),text,'Trimmed to', op_file)
                    op_file_path = os.path.join(op_path, op_file)
                # op_file_path += ext
                print(ins(), ' (' , done_count ,'T'+str(self.num) ,') ' ,i, '->',op_file+ext)
                # shutil.copy(j, op_file_path)
                shutil.move(new_path, op_file_path) # Move the file from Temp Thread Location to output folder
                done_count += 1
                print()
            except KeyboardInterrupt:
                print('Exiting')
                kill = True
                os._exit(0)
                break;
            except:
                print(ins(),'Error for', i)
                traceback.print_exc()
                err_str += i + ' :: ' + traceback.format_exc()+ "\n"
                err_count += 1

num_threads_arr = []
div = int(len(lis)/num_threads+1)
o,p = 0,0
for n in range(num_threads):
    p = o+div
    if p > len(lis): p = None
    num_threads_arr.append([o,p])
    o = p

print(num_threads_arr)

class Input(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global pause, kill, slow, delay
        print('Ready for input')
        while True:
            try:
                if kill:
                    print("Exiting", ins())
                    os._exit(0)
                st = ''
                st = raw_input() if not p3 else input() # for raw string input
                print('st:', st)
                if st.lower() == 'exit' : # exit
                    kill = True
                    print('Exiting', ins())
                    os._exit(0)
                elif st.lower() == 'p':
                    pause = not pause
                    print('Pause:', pause)
                else:
                    delay += (float(st.count('+')) - float(st.count('-')))/250 # delay changes proportionally to number of plus / minus found (2ms per count)
                    delay = round(constrain(delay,0, 3),3) # constraints offset to limits
                print('Curr delay ' , delay)
            except KeyboardInterrupt:
                print('Exiting')
                kill = True
                os._exit(0)
                break;
            except :
                traceback.print_exc()


thrs= []
try :
    if __name__ == '__main__':
        for num, th in enumerate(num_threads_arr):
            thrs.append(Index(lis[th[0]:th[1]], num))
            thrs[-1].start()
            inp = Input()
            inp.start()
except :
    traceback.print_exc()


for th in thrs:
    th.join()

print(ins(),'Done:', done_count ,'/',eligible_count)
print(ins(),'Error:', err_count ,'/',eligible_count)
print(ins(),'NA:', na_count ,'/',eligible_count)
# print(ins(),'All done')

print(ins(), err_str)
kill = True
os._exit(0)
