# -*- coding: utf-8 -*-
import re
import os
import json
import sys

sys.path.append(os.path.abspath('./'))
from enumFile import enumfile,getFileType,getFullPath
from searchZh import isJsonFile

def formatJson(root):
    files = os.listdir(root)
    print(files)
    for f in files:
        # if os.path.isdir(f):
        #     formatJson(getFullPath(root,f))
        if not isJsonFile(f):
            print ('不是json{}'.format(f))
            continue
        filecp = f+'_formatjson'
        with(open(f,'r',encoding = 'utf-8')) as printF:
                jsonDt = json.load(printF)
                with(open(filecp,'w',encoding = 'utf-8')) as outf:
                    json.dump((jsonDt),outf,sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False)
        print('格式化文件',f)
        os.remove(f)
        os.rename(filecp,f)
    pass

if __name__ == "__main__":
    formatJson('./')
    pass