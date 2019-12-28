# -*- coding: utf-8 -*-
import re
import os
import json
import sys

sys.path.append(os.path.abspath('./'))
from enumFile import enumfile,getFileType,getFullPath
from searchZh import isJsonFile

def formatJson(root):
    absP = os.path.abspath(root)
    files = os.listdir(absP)
    # print (absP)
    # print(files)
    for f in files:
        fullN = getFullPath(root,f)
        if os.path.isdir(fullN):
            # pass
            formatJson(fullN)
        else :
            if isJsonFile(fullN) is False:
                # print ('不是json{}'.format(fullN))
                continue
            filecp = fullN+'_formatjson'
            with(open(fullN,'r',encoding = 'utf-8')) as printF:
                    jsonDt = json.load(printF)
                    with(open(filecp,'w',encoding = 'utf-8')) as outf:
                        json.dump((jsonDt),outf,sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False)
            print('格式化文件',fullN)
            os.remove(fullN)
            os.rename(filecp,fullN)
    pass

if __name__ == "__main__":
    formatJson('./..')
    pass