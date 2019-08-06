import os, sys, time
from PIL import Image, ImageEnhance
import argparse, inspect, datetime, shutil, traceback
from pathvalidate import sanitize_filepath
from threading import Thread


num_threads = 4
max_path_len = 254
p3 = sys.version_info > (2,8)

pause = False
def ins():
    return inspect.getframeinfo(inspect.stack()[1][0]).lineno # For debugging, print line number which called this function

def Sort(lis, ind):
    return sorted(lis, key=lambda x: x[ind])

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path",required=False, help='Give path name' )
parser.add_argument("-nd", "--npdict",required=False, action="store_true", dest='nodict', help='If dictionary to be used' )
parser.add_argument("-f", "--filter",required=False,nargs='*', help='Filter' )
parser.add_argument("-ef", "--excludefilter",required=False, nargs='*', help='Exclusion filter' )

cmd_args  = parser.parse_args()
print(ins(), cmd_args)

if not cmd_args.nodict:
    print('Using dictionary')
    import enchant
    d = enchant.Dict("en_US")

path = cmd_args.path if cmd_args.path != None else os.getcwd()
print(ins(),'Using path :')

if not os.path.isdir(path):
    print('invalid path\nExiting')
    sys.exit(1)

err_str = ''
op_folder='output_' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
thresh = [240, 220, 200, 150, 100, 50, 25]
# thresh = [240, 220, 200, 150, 100, 50, 25]

lis = os.listdir(path)
op_path = os.path.join(path,op_folder)
print('Output path = ', op_path)
os.mkdir(op_path)
print('Created Dir')
# lis_p = map(lambda x:os.path.join(path,x),lis)
if len(op_path) > max_path_len-8:
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
        self.pyt = pyter
        Thread.__init__(self)

    def run(self):
        global max_path_len, cmd_args, path, err_str, op_folder, pause
        global thresh, done_count, err_count, eligible_count, na_count
        print(ins(), self.num, len(self.sub_lis))
        # time.sleep(2)
        # print(ins(), self.num, len(self.sub_lis))
        # sys.exit(0)
        op_temp_path = os.path.join(op_path, 'temp_T'+str(self.num))
        os.mkdir(op_temp_path)
        os.chdir(op_temp_path)
        for i in self.sub_lis:
            try:
                while pause:
                    time.sleep(0.5)
                ext = i.split('.')[-1]
                if ext.lower() not in ['png', 'jpg', 'jpeg', 'bmp']:
                    print('Skipping',i )
                    continue
                j = os.path.join(path,i)
                new_path = os.path.join(op_temp_path, i)
                shutil.copy(j, new_path)
                eligible_count += 1
                img_o = Image.open(new_path)
                contrast = ImageEnhance.Contrast(img_o)
                img = contrast.enhance(1.2)
                sharp = ImageEnhance.Sharpness(img)
                img = sharp.enhance(1.2)
                words = []
                for thres in thresh:
                    fn = lambda x : 255 if x > thres else 0
                    img_t = img.convert('L').point(fn, mode='1');
                    # pytesseract.image_to_string(img, lang='eng',config='-psm 0 txt')
                    text = self.pyt.image_to_string(img_t, lang='eng')
                    # text = pytesseract.image_to_string(img_t, lang='eng')
                    # pytesseract.image_to_string(contrast.enhance(2).convert('L').point(fn, mode='1'))
                    dcount = 0
                    if text == '': text = 'NA_'+i; dcount -= 255
                    text = sanitize_filepath(text)
                    text = text.replace('/', '').replace(' ', '_')
                    text = '_'.join([t for t in text.split('_') if t])
                    for w in text.split('_'):
                        if w == '': continue
                        if not cmd_args.nodict:
                            if d.check(w.lower()): dcount +=1
                            # d.suggest("Helo")
                        else: dcount +=1; #print(w);
                    words.append((thres, text, dcount))
                    print('T'+str(self.num), dcount, 'Thresh:', thres, text )
                words = Sort(words,2)
                text = words[-1][1]
                ext = '.' + ext
                if text == 'NA_' + i : na_count += 1; op_file = text
                else : op_file = text + ext
                op_file_path = os.path.join(op_path, op_file)
                diff = len(op_file_path+ext) - max_path_len
                # print(ins(), diff)
                if diff  > 0:
                    # op_file_path = op_file_path[:251]
                    op_file = op_file[:-diff-len(ext)] + ext
                    print(ins(),text,'Trimmed to', op_file)
                    op_file_path = os.path.join(op_path, op_file)
                # op_file_path += ext
                print(ins(),i, '->',op_file+ext, ' (' , done_count ,'T'+str(self.num) ,')')
                # shutil.copy(j, op_file_path)
                shutil.move(new_path, op_file_path)
                done_count += 1
                print()
            except KeyboardInterrupt:
                print('Exiting')
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
        global pause, kill, slow
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
                elif st.lower() = 'p':
                    pause = !pause
                print('Curr offset ' , offset)
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
print(ins(),'All done')

print(ins(), err_str)
