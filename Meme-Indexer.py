import os, pytesseract, sys
from PIL import Image, ImageEnhance
import argparse, inspect, datetime, shutil, traceback
from pathvalidate import sanitize_filepath


#73, 146 mins pre multi threading

max_path_len = 254
p3 = sys.version_info > (2,8)

def ins():
    return inspect.getframeinfo(inspect.stack()[1][0]).lineno # For debugging, print line number which called this function

def Sort(lis, ind):
    return sorted(lis, key=lambda x: x[ind])

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path",required=False, help='Give path name' )
parser.add_argument("-nd", "--npdict",required=False, action="store_true", dest='nodict', help='If dictionary to be used' )
# parser.add_argument("-f", "--filter",required=False,nargs='*', help='Filter' )
# parser.add_argument("-ef", "--excludefilter",required=False, nargs='*', help='Exclusion filter' )

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

for i in lis:
    try:
        ext = i.split('.')[-1]
        if ext.lower() not in ['png', 'jpg', 'jpeg', 'bmp']:
            print('Skipping',i )
            continue
        eligible_count += 1
        j = os.path.join(path,i)
        img_o = Image.open(j)
        contrast = ImageEnhance.Contrast(img_o)
        img = contrast.enhance(1.2)
        sharp = ImageEnhance.Sharpness(img)
        img = sharp.enhance(1.2)
        words = []
        for thres in thresh:
            fn = lambda x : 255 if x > thres else 0
            img_t = img.convert('L').point(fn, mode='1');
            # pytesseract.image_to_string(img, lang='eng',config='-psm 0 txt')
            text = pytesseract.image_to_string(img_t, lang='eng')
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
            print('Thresh:', thres, text, dcount)
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
        print(ins(),i, '->',op_file+ext, ' (' , done_count , ')')
        shutil.copy(j, op_file_path)
        done_count += 1
    except KeyboardInterrupt:
        print('Exiting')
        break;
    except:
        print(ins(),'Error for', i)
        traceback.print_exc()
        err_str += i + ' :: ' + traceback.format_exc()+ "\n"
        err_count += 1


print(ins(),'Done:', done_count ,'/',eligible_count)
print(ins(),'Error:', err_count ,'/',eligible_count)
print(ins(),'NA:', na_count ,'/',eligible_count)
print(ins(),'All done')

print(ins(), err_str)
