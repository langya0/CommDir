# -*- coding: utf-8 -*-
import re
import os
import getopt
import json
import sys

sys.path.append(os.path.abspath('./'))
from enumFile import enumfile,getFileType,getFullPath

# 方案：
# 1、针对ui，场景文件，json解析拿到中文
# 2、针对代码文件，对编译好的文件，忽略注释，提取中文

## 需要关注的文件列表 ui+代码
flgFilesNeedCheck = ['ui','json','scene','prefab','as'] #'.ts','.json','.as','.html','.scene','.prefab' 
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
## 提取的包含中文文件列表
desFileHasZhSet = set()

## 中文及文件关系   file:中文
fileWordDict = dict()

## 中文提取配置表； id:中文
outWordDict = {}
## 中文提取配置表； 中文:id
outWordDictRe = {}
debug = False

## 拿到的所有中文集合
zhSet = set()
## 注释集合
com = []

logFileName = 'guojihua.log'
i18JsonOutFile = "i18n.json"
i18nCfgFile = "i18ncfg.json"

## 文件枚举    
def listfile(root):
    def pushFilePathInList(f):
        if(f in publishJsFiles):
            srcPublishFiles.append(f)
        else:
            srcFileList.append(f)
    ign = []
    ign.append(logFileName)
    ign.append(i18JsonOutFile)
    ign.append(i18nCfgFile)
    enumfile(root,cbFun=pushFilePathInList,ignorDir=flgIgnorDirs,includeType=flgFilesNeedCheck,ignorFileList=ign)

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
# 做代码处理，这里还要考究
def parseLine(line,notValue=True):
    re_words = ''
    if(notValue):
        re_words = re.compile(u"[\"']+.*?[\u4e00-\u9fa5]+.*[\u4e00-\u9fa5]+.*?['\"]")
    else:
        re_words = re.compile(u".*[\u4e00-\u9fa5]+.*")  #json结构需要考虑整个串
    m = re.findall(re_words,line)
    if m and not checkIsComment(line):
        for x in m:
            ll = x.split(':')
            if len(ll) > 1 and notValue:    ## + and notValue json 不能分割
                [parseLine(p) for p in ll]
            else :
                zhSet.add(x.strip('"').strip('\''))
        return True
    return False

logF = open(logFileName,'w')
# 日志输出
def LogStep(ar1, *d, **s):
    if debug:
        print('\n{}{}\n'.format('>>>',ar1))
    else:
        logF.write('\n{}{}\n'.format('>>>',ar1))
def LogCoreInfo(ar1, *d, **s):
    if debug:
        print('{}{}\n'.format('##',ar1))
    else:
        logF.write('{}{}\n'.format('##',ar1))
def logEnum(ar1, *d, **s):
    if debug:
        print('{}\n'.format(ar1))
    else:
        logF.write('{}\n'.format(ar1))
def logTryError(ar1, *d, **s):
    if debug:
        print('{}\n'.format(ar1))
    else:
        logF.write('{}\n'.format(ar1))

# 处理所有json文件
def parseJsonFile(jsonDt,f):
    if(isinstance(jsonDt,list)):
        jsonDt = [parseJsonFile(item,f) for item in jsonDt]
    elif(isinstance(jsonDt,str)):
        if(parseLine(jsonDt,False)):
            if f not in fileWordDict.keys():
                fileWordDict[f] = []
            fileWordDict[f].append(jsonDt)
            desFileHasZhSet.add(f)
    elif(isinstance(jsonDt,dict)):
        items = jsonDt.items()
        for key, value in items:
            # 这里有个问题。key为汉字是否需要处理   目前仅针对成语
            if(key not in flgIgnorKeys):
                parseJsonFile(key,f)    #处理中文key
                jsonDt[key] = parseJsonFile(value,f)
    return jsonDt

def isJsonFile(f):
    try:
        with(open(f,'r',encoding = 'utf-8')) as outF:
            json.load(outF)
            return True
    except:
        return False

def checkFiles(f):
    isJson = isJsonFile(f)
    with(open(f,'r',encoding = 'utf-8')) as outF:
        # json文件
        if(isJson and 1):
            jsonDt = json.load(outF)
            retDt = parseJsonFile(jsonDt,f)
            # 最后做替换，这里忽略
            # if f in desFileHasZhSet:
            #     with(open(f + '._des','w',encoding = 'utf-8')) as printF:
            #         json.dump(retDt,printF,sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False)
        # 代码文件
        else:
            lines = outF.readlines()
            for i, line in enumerate(lines):
                if(parseLine(line)):
                    if f not in fileWordDict.keys():
                        fileWordDict[f] = []
                    if(-1 == line.find('.uiView=')) and 1:  # ui文件的生成中文
                        fileWordDict[f].append(line)
                        desFileHasZhSet.add(f)
                        lines[i] = '----' + os.linesep  #这里做考虑做替换
            if f in desFileHasZhSet:
                with(open(f + '._des','w',encoding = 'utf-8')) as printF:
                    printF.writelines(lines)
            pass
    if(f in desFileHasZhSet):
        LogStep('检查文件类型   有中文  {}  #json= {}\n{}'.format((os.path.basename(f)),isJson,f))
        LogCoreInfo('文件内容中文'+ str(fileWordDict[f]))


def start():
    os.system('cls')

    ## 枚举文件
    LogStep('枚举所有文件')
    listfile('./..')
    LogStep('所有[代码生成文件]列表')
    [logEnum(x) for x in srcPublishFiles]
    LogStep('所有[源文件]列表')
    [logEnum(x) for x in srcFileList]
    LogStep('遍历提取[代码生成文件]中的中文')
    [checkFiles(f) for f in srcPublishFiles]
    
    LogStep('遍历提取[源文件]中的中文')
    [checkFiles(f) for f in srcFileList]

    LogStep('所有中文')
    [logEnum(x) for x in zhSet]
    LogStep('所有包含中文的注释')
    [logEnum(x) for x in com]

    LogStep('文件-中文关系')
    logEnum(json.dumps(fileWordDict,ensure_ascii=False,indent=4))
    outWriteZhMapTab()

    LogStep('更新源json系列文件')
    updateJsonFiles()
    pass

zhCheckRe = re.compile(u".*[\u4e00-\u9fa5]+.*")  #json结构需要考虑整个串
#记录处理json调整
strNeedChange = ""

# json文件中文替换
parseingF = ""
def parseJson(jsonDt,parent=None):
    if(isinstance(jsonDt,list)):
        for i,item in enumerate( jsonDt):
            jsonDt[i] = parseJson(item)
            parent = jsonDt[i]
        jsonDt = [parseJson(item) for item in jsonDt]
    elif(isinstance(jsonDt,dict)):
        items = jsonDt.items()
        parent = jsonDt
        ned = False
        for key, value in items:
            jsonDt[key] = parseJson(value)
            if isinstance(value,str):
                x = re.findall(zhCheckRe,value)
                if x:
                    strNeedChange = x[0]
                    ned = True
                    jsonDt[key] = ""    # 删掉中文
        if(ned):
            try:
                parent['DataID'] = outWordDictRe[strNeedChange]    #替换为ID
            except:
                logTryError('中文替换异常 文件 {},中文  {}'.format(parseingF,strNeedChange))
    return jsonDt

import shutil

## 更新源json-ui文件。清空中文，增加控件i18
def updateJsonFiles():
    # 检查包含中文
    def checkLineHasZh(line):
        re_words = re.compile(u".*[\u4e00-\u9fa5]+.*")  #json结构需要考虑整个串
        m = re.findall(re_words,line)
        if m:
            return m
        return [""]
    for f in desFileHasZhSet:
        if(isJsonFile(f)):
            copyF = f+'copy'
            with(open(f,'r',encoding = 'utf-8')) as printF:
                jsonDt = json.load(printF)
                parseingF = f
                jsonDt = parseJson(jsonDt,parent=None)
                with(open(copyF,'w',encoding = 'utf-8')) as outf:
                    json.dump((jsonDt),outf,sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False)
            ## TODO 做文件替换
            LogStep('重命名替换文件{}'.format(f))
            os.remove(f)
            os.rename(copyF,f)
            # (copyF,f)
    pass


def outWriteZhMapTab():
    with(open(i18JsonOutFile,'w',encoding = 'utf-8')) as printF:
        for i, val in enumerate(zhSet):
            outWordDict [str(i).zfill(4)] =val 
            outWordDictRe [val]=str(i).zfill(4)
        json.dump((outWordDict),printF,sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False)

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "d", ["debug"])
    for opt_name,opt_value in opts:
        if opt_name in ('-d','--debug'):
            debug = True

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