# -*- coding: utf-8 -*-
import re
import os
import getopt
import json
import sys
# 方案：
# 1、针对ui，场景文件，json解析拿到中文
# 2、针对代码文件，对编译好的文件，忽略注释，提取中文

## 需要关注的文件列表json
flgFilesNeedCheck = ['.js','.json','.scene','.prefab'] #'.ts','.json','.as','.html','.scene','.prefab' 
## 可以忽略的文件夹
flgIgnorDirs = ['release','libs','tools','2313','.git','.gitignore','.laya','.rpt2_cache']  
## 场景文件，需要忽略的标签
flgIgnorKeys = ['labelFont','font'] 
## 代码编译好的js文件，提取代码中有效中文
publishJsFiles = ['Main.max.js']

#################################################################
## 遍历得到的源文件 在flgFilesNeedCheck范围内
srcFileList = []   
## 编译生成的文件列表，用于提取需要处理的关键中文
srcPublishFiles = []
## 提取的中文文件列表
desFileHasZhSet = set()

## 文件枚举    
def listfile(root):
    files = os.listdir(root)
    for f in files:
        fullNm = os.path.abspath(root) + os.path.sep+ f
        if not os.path.isdir(fullNm):
            if os.path.isfile(fullNm) and (os.path.splitext(fullNm)[1]) in flgFilesNeedCheck:
                baseName = os.path.basename(fullNm)
                if(baseName in publishJsFiles):
                    srcPublishFiles.append(fullNm)
                else:
                    srcFileList.append(fullNm)
        else:
            if  f in flgIgnorDirs:
                print('忽略目录',f)
                continue
                pass
            else :
                listfile(fullNm)

    # for root, dirs, files in os.walk(root):
    #     for x in ignorDir:
    #         if(root.endswith(x)):
    #             print('目录忽略',root)
    #             continue
    #     for f in files:
    #         fullNm =  os.path.abspath(root) + os.path.sep+ f
    #         if (os.path.splitext(fullNm)[1]) in fileFlg:
    #             fileList.append(fullNm)
    #     pass

## 使用说明
def help():
    print("""
usage: [-h | --help] >> 显示帮助
usage: [-l | --listfile] >> 罗列需要处理的信息
        """)

## 拿到的所有中文集合
zhSet = []

## 注释集合
com = []

## 格式化文件是否为注释
def checkIsComment(line):
    coreStr = line.strip()
    if coreStr.find('//') == 0:
        com.append(coreStr)
        return True
    if coreStr.find('*') == 0:
        com.append(coreStr)
        return True
    if coreStr.find('/*') == 0:
        com.append(coreStr)
        return True
    if coreStr.find('*/') == 0:
        com.append(coreStr)
        return True
    return False
    pass

# 检查行是否包含中文,notValue:是否为 key-value的value 即不包含"
def parseLine(line,notValue=True):
    re_words = ''
    if(notValue):
        re_words = re.compile(u"[\"']+.*?[\u4e00-\u9fa5]+.*[\u4e00-\u9fa5]+.*?['\"]")
    else:
        re_words = re.compile(u"[\u4e00-\u9fa5]+")
    m = re.findall(re_words,line)
    if m and not checkIsComment(line):
        for x in m:
            ll = x.split(':')
            if len(ll) > 1:
                [parseLine(p) for p in ll]
            else :
                zhSet.append(x.strip('"').strip('\''))
        return True
    return False

# 日志输出
def LogStep(ar1, *d, **s):
    print('\n{}{}'.format('>>>',ar1))
def LogCoreInfo(ar1, *d, **s):
    print('{}{}'.format('##',ar1))

# 处理所有json文件
def parseJsonFile(jsonDt,f):
    if(isinstance(jsonDt,list)):
        jsonDt = [parseJsonFile(item,f) for item in jsonDt]
    elif(isinstance(jsonDt,str)):
        # print(jsonDt)
        if(parseLine(jsonDt,False)):
            LogCoreInfo('zh>> '+jsonDt)
            desFileHasZhSet.add(f)
            jsonDt = 'langya5230_1'
    elif(isinstance(jsonDt,dict)):
        items = jsonDt.items()
        for key, value in items:
            # 这里有个问题。key为汉字是否需要处理   目前仅针对成语
            if(key not in flgIgnorKeys):
                jsonDt[key] = parseJsonFile(value,f)
    else:
        pass
    return jsonDt
    pass

def isJsonFile(f):
    try:
        with(open(f,'r',encoding = 'utf-8')) as outF:
            json.load(outF)
            return True
    except:
        return False

lambda x:x+x
def checkFiles(f):
    # print ('\n--------------------------------------------------\n####[checkFile....]',f)
    isJson = isJsonFile(f)
    LogStep('检查文件类型json= {}\n{}\n'.format(isJson,f))
    with(open(f,'r',encoding = 'utf-8')) as outF:
        if(isJson and 1):
            jsonDt = json.load(outF)
            retDt = parseJsonFile(jsonDt,f)
            if f in desFileHasZhSet:
                with(open(f + '._des','w',encoding = 'utf-8')) as printF:
                    json.dump(retDt,printF,sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False)
        else:
            lines = outF.readlines()
            for i, line in enumerate(lines):
                if(parseLine(line)):

                    # print('ssssssss---------------',line.find('.uiView='))
                    if(-1 == line.find('.uiView=')):
                        print(line)
                        desFileHasZhSet.add(f)
                        lines[i] = '----' + os.linesep
            if f in desFileHasZhSet:
                with(open(f + '._des','w',encoding = 'utf-8')) as printF:
                    printF.writelines(lines)
            pass
        # [(CheckLine(line)) for line in outF.readlines()]

def start():
    os.system('cls')

    ## 枚举文件
    LogStep('枚举所有文件')
    listfile('./')
    LogStep('所有[代码生成文件]列表')
    [print(x) for x in srcPublishFiles]
    LogStep('所有[源文件]列表')
    [print(x) for x in srcFileList]
    LogStep('遍历提取[代码生成文件]中的中文')
    [checkFiles(f) for f in srcPublishFiles]
    LogStep('遍历提取[源文件]中的中文')
    [checkFiles(f) for f in srcFileList]

    LogStep('所有中文')
    [print(x) for x in zhSet]
    LogStep('所有包含中文的注释')
    [print(x) for x in com]
    pass

if __name__ == '__main__':
    start()


# def optHelp():
#     # print (fileList)
#     pass
#     try:
#         opts, args = getopt.getopt(sys.argv[1:], "lihf", ["ignor","help","file="])
#         for opt_name,opt_value in opts:
#             if opt_name in ('-h','--help'):
#                 help()
#                 sys.exit()
#             if opt_name in ('-l'):
#                 listfile(args[0])

#                 print ('--------------')
#                 print (srcFileList)
#                 sys.exit()
#     except getopt.GetoptError:
#         print('getopt.GetoptError')
#         pass