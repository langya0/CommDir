# -*- coding: utf-8 -*-
import re
import os
def getFileType(baseName):
    '获取文件后缀'
    try:
        return os.path.splitext(baseName)[1][1:]
    except:
        return ""

def getFullPath(rootPath,baseName):
    '获取文件绝对路径'
    return os.path.abspath(rootPath) + os.path.sep+ baseName

def enumfile(rootPath,cbFun = None,ignorDir=[],includeType=[],ignorFileList=[]):
    """
    枚举文件，
    cbFun:回调
    ignorDir:忽略目录列表
    includeType:需要检测的文件列表，如'.js'
    """
    files = os.listdir(rootPath)
    for f in files:
        fullNm = getFullPath(rootPath,f)
        if os.path.isdir(fullNm) and f not in ignorDir:
            enumfile(fullNm,cbFun,ignorDir,includeType,ignorFileList)
        if(not os.path.isdir(fullNm)) and os.path.basename(f) not in ignorFileList and getFileType(f) in includeType:
            cbFun and cbFun(fullNm)

def out(f):
    print('file:{},type:{},'.format(f,getFileType(f)))

if __name__ == "__main__":
    print('uni_test------------------------------')
    enumfile('./',out)
    print('uni_test------------------------------')
    enumfile('./',out,ignorDir=['123'],includeType=['_des'],ignorFileList=['enumfile.py'])
    # enumfile('./',test)