# -*- coding: utf-8 -*-
import os
import sys
import getopt
import time

root_path = ""
web_path = ""

# 1、拖拽？拿到路径
# 2、发布
# 3、压缩资源
def renameDir(newDir,fileName):
    # newNm = time.strftime("%Y%m%d", time.localtime(time.time()))
    # resultInfo('renameDir'+newDir+'>>'+newNm)

    # if(os.path.exists(newDir + newNm)):
    #     newNm =newNm +'_a'
    #     # pass

    # os.rename(newDir + fileName,newNm)
    # print(result)
    pass

# def gitUpdate():
    # print (__doc__)

def resultInfo(msg):
    print(sys._getframe().f_code.co_name)


if(__name__ == "__main__"):
    opts,args = getopt.getopt(sys.argv[1:],'',[])
    root_path = args[0]

    os.chdir(root_path)
    resultInfo('chdir(root_path)'+root_path)


    # resu = os.system('git pull')
    # print(resu)

    web_path = os.getcwd() + os.sep+ 'release' + os.sep+ 'layaweb' + os.sep

    if(not os.path.exists(web_path)):
        os.makedirs(web_path)
    # gitUpdate()
    # 旧目录
    preDirs = []
    for p in os.listdir(web_path):
        # print(p)
        if os.path.isdir(web_path + os.sep + p):
            resultInfo(p)
            preDirs.append(p)

    newDir = ""

    result = os.system("""layaair-cmd publish --noUi --noAtlas -o cc -n 1000""")

    for p in os.listdir(web_path):
        if(p not in preDirs):
            newDir = p
    
    resultInfo (newDir)
    resultInfo('newDir'+newDir)

    os.chdir(web_path)
    resultInfo('chdir(web_path)'+web_path)
    renameDir(web_path + os.sep, newDir)
    # os.system("pause")
    pass
## js项目编译
## E:\engineering\HappySoccer\.laya\astool\layajs.exe e:\engineering\HappySoccer\.actionScriptProperties;iflash=false;chromerun=false;