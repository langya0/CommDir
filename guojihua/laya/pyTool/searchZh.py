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

#################################################################
## 默认配置部分 
## 需要关注的文件列表 ui+代码
flgFilesNeedCheck = ['ui','json','scene','prefab','as','js','ts'] #'.ts','.json','.as','.html','.scene','.prefab' 
## 可以忽略的文件夹
flgIgnorDirs = ['release','libs','tools','2313','.git','.gitignore','.laya','.rpt2_cache']  
## 场景文件，需要忽略的标签
flgIgnorKeys = ['labelFont','font'] 
## 代码编译好的js文件，提取代码中有效中文
publishJsFiles = ['Main.max.js','bundle.js','code.js']
## log标签
logFlgNeedIgnor = ['LogUtil','console.log','console.info','console.error','console.warn','console.debug','throw'] 

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
## 代码生成文件中文集合，用来筛选代码中需要处理的中文
zhSetInPublishFile = set()
## 注释集合
com = []

# 正在处理中的文件
workingF = ""   

logFileName = 'guojihua.log'
i18JsonOutFile = "i18n.json"
i18nCfgFile = "i18ncfg.json"

# ""部分包含中文
reZhWithFlg = re.compile(u"[\"'].*?[\u4e00-\u9fa5]+.*?['\"]") # 解决未匹配到单字问题
# 包含中文即可
reJustHasZh = re.compile(u".*[\u4e00-\u9fa5]+.*")  #json结构需要考虑整个串

## 异常信息记录
tryErrorInfoLis= []

#################################################################
## 加载配置文件
def loadCfgFile():
    with(open(i18nCfgFile,'r',encoding = 'utf-8')) as outF:
        jsDt = json.load(outF)
        if jsDt['typeFileNeedCheck'] and jsDt['typeFileNeedCheck']['list']:
            flgFilesNeedCheck = jsDt['typeFileNeedCheck']['list']
        if jsDt['dirsIgnor'] and jsDt['dirsIgnor']['list']:
            flgIgnorDirs = jsDt['dirsIgnor']['list']
        if jsDt['flgIgnorInJsonFile'] and jsDt['flgIgnorInJsonFile']['list']:
            flgIgnorKeys = jsDt['flgIgnorInJsonFile']['list']
        if jsDt['filePublish'] and jsDt['filePublish']['list']:
            publishJsFiles = jsDt['filePublish']['list']
        if jsDt['flgIgnorLog'] and jsDt['flgIgnorLog']['list']:
            logFlgNeedIgnor = jsDt['flgIgnorLog']['list']
        logEnum(str(jsDt))        
    
## 加载已有中文配置项，向后兼容
def loadOldZhCfg():
    tryErr = 1
    try:
        with(open(i18JsonOutFile,'r',encoding = 'utf-8')) as outF:
            jsdt = json.load(outF)
            for x in jsdt:
                outWordDict[(x)] = jsdt[x]
                outWordDictRe[jsdt[x]] = (x)
                zhSet.add(jsdt[x])
            logEnum(str(outWordDict))
            logEnum(str(outWordDictRe))
            
    except FileNotFoundError:
        logTryError('无旧中文')
        pass
    except json.decoder.JSONDecodeError:
        logTryError('json解析异常')
        pass

## 文件枚举    
def listfile(root):
    def pushFilePathInList(f):
        if(os.path.basename(f) in publishJsFiles):
            srcPublishFiles.append(f)
        else:
            srcFileList.append(f)
    ign = []
    ign.append(logFileName)
    ign.append(i18JsonOutFile)
    ign.append(i18nCfgFile)
    enumfile(root,cbFun=pushFilePathInList,ignorDir=flgIgnorDirs,includeType=flgFilesNeedCheck,ignorFileList=ign)

## 是否应当忽略
def needIgnor(line):
    if len(line) > 200:
        return True
    if checkIsComment(line) or checkIsLog(line) or line.find('.uiView=')!=-1:
        return True
    return False

## 是否为日志相关
def checkIsLog(line):
    coreStr = line.strip()
    for x in logFlgNeedIgnor:
        if coreStr.find(x) == 0:
            return True
    return False

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

def getSubStrSplit(line):
    l1 = line.split('\'')
    ret = []
    aaa = []
    for x in l1:
        s =x.split('"')
        for a in s:
            aaa.append(a)
    for i, v in enumerate(aaa):
        if i % 2 ==1:
            ret.append(v)
    
    return ret

# 检查行是否包含中文,notValue:是否为 key-value的value 即不包含"
# 做代码处理，这里还要考究
def parseLine(line,isValue = False):
    if needIgnor(line):
         return False
         
    if isValue:
        line = '"{}"'.format(line)

    r = getSubStrSplit(line)
    if not r:
        return False

    ret = False
    for x in r:
        m = re.findall(reJustHasZh,x)
        if m:
            ret = True
        for x in m:
            zhSet.add(x.strip('"').strip('\''))
            if(os.path.basename(workingF) in publishJsFiles):
                zhSetInPublishFile.add(x.strip('"').strip('\''))
    return ret

logF = open(logFileName,'w')
# 日志输出
def LogStep(ar1, *d, **s):
    if debug:
        print('\n{}{}\n'.format('重要节点>>>>>',ar1))
    else:
        logF.write('\n{}{}\n'.format('重要节点>>>>>',ar1))
def logEnum(ar1, *d, **s):
    if debug:
        print('>> {}\n'.format(ar1))
    else:
        logF.write('{}\n'.format(ar1))
def logTryError(ar1, *d, **s):
    if debug:
        print('#####ERROR{}\n'.format(ar1))
    else:
        logF.write('{}\n'.format(ar1))

# 处理所有json文件
def parseJsonFile(jsonDt,f):
    if(isinstance(jsonDt,list)):
        jsonDt = [parseJsonFile(item,f) for item in jsonDt]
    elif(isinstance(jsonDt,str)):
        if(parseLine(jsonDt,True)):
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
    global workingF
    workingF = f
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
                    fileWordDict[f].append(line)
                    desFileHasZhSet.add(f)
            # if f in desFileHasZhSet:
            #     with(open(f + '._des','w',encoding = 'utf-8')) as printF:
            #         printF.writelines(lines)
            pass
    if(f in desFileHasZhSet):
        LogStep('检查文件类型   有中文  {}  #json= {}\n{}'.format((os.path.basename(f)),isJson,f))
        logEnum('文件内容中文'+ str(fileWordDict[f]))

#记录处理json调整
strNeedChange = ""
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
            if(key in flgIgnorKeys):
                continue
            jsonDt[key] = parseJson(value)
            if isinstance(value,str):
                x = re.findall(reJustHasZh,value)
                if x:
                    strNeedChange = x[0]
                    ned = True
                    jsonDt[key] = ""    # 删掉中文
        if(ned):
            try:
                parent['DataID'] = outWordDictRe[strNeedChange]    #替换为ID
            except:
                logTryError('中文替换异常 文件 {},中文  {}'.format(workingF,strNeedChange))
    return jsonDt

import shutil

## 更新源json-ui文件。清空中文，增加控件i18
def updateJsonFiles():
    # 检查包含中文
    def checkLineHasZh(line):
        m = re.findall(reJustHasZh,line)
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

## 更新替换代码文件
def updateCodeFiles():
    for f in desFileHasZhSet:
        if(os.path.basename(f) in publishJsFiles):
            continue
        LogStep('重命名替换[代码]文件{}'.format(f))
        if(not isJsonFile(f)):
            copyF = f+'.copy'
            linesCp = []
            with(open(f,'r',encoding = 'utf-8')) as printF:
                lines = printF.readlines()
                for line in lines:
                    if needIgnor(line):
                        linesCp.append(line)
                        continue
                    # 忽略行尾注释
                    a = line.split("//")
                    if(not a):
                        linesCp.append(line)
                        continue

                    m = getSubStrSplit(a[0])
                    errInfo = ""
                    for x in m:
                        errInfo = ""
                        if x in zhSetInPublishFile:
                            try :
                                reCheckZh = re.compile(u"[\'\"]{}[\'\"]".format(x))  
                                for l in re.findall(reCheckZh,line):
                                    line = line.replace(l,'window[\'i18nHelp\'].getStrById(\"{}\")'.format(outWordDictRe[x]))
                            except KeyError:
                                errInfo = 'error,{}------{}'.format(x,line)
                                tryErrorInfoLis.append(errInfo)
                                pass
                            except re.error:
                                errInfo = 'error,{}------{}'.format(x,line)
                                tryErrorInfoLis.append(errInfo)
                                pass
                            if errInfo:
                                logTryError(errInfo)
                            continue
                    linesCp.append(line)
            with(open(copyF,'w',encoding = 'utf-8')) as outf:
                logEnum('写入文件：{}'.format(copyF))
                outf.writelines(linesCp)
            os.remove(f)
            os.rename(copyF,f)

## 将生成的 id:中文 写入文件
def outWriteZhMapTab():
    with(open(i18JsonOutFile,'w',encoding = 'utf-8')) as printF:
        i = 0
        existIndex = []
        allIndex = []
        for val in zhSet:
            if val in outWordDictRe:
                allIndex.append(int(outWordDictRe[val]))
                existIndex.append(int(outWordDictRe[val]))
                continue
            while str(i).zfill(5) in outWordDict:
                i = i + 1

            outWordDict [str(i).zfill(5)] =val 
            outWordDictRe [val]=str(i).zfill(5)
        outWordDict.sort()
        json.dump((outWordDict),printF,sort_keys=False, indent=4, separators=(',', ': '),ensure_ascii=False)

def start():
    os.system('cls')

    LogStep('加载配置文件')
    loadCfgFile()
    LogStep('加载已有中文信息')
    loadOldZhCfg()

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

    logEnum("########################################################")
    LogStep('所有中文')
    [logEnum(x) for x in zhSet]
    LogStep('所有包含中文的注释')
    [logEnum(x) for x in com]
    logEnum("########################################################")

    LogStep('文件-中文关系')
    logEnum(json.dumps(fileWordDict,ensure_ascii=False,indent=4))
    outWriteZhMapTab()

    LogStep('更新源json系列文件')
    updateJsonFiles()
    LogStep('更新源非json系列文件-代码等')
    updateCodeFiles()

    LogStep('记录部分异常场景')
    [logEnum(x) for x in tryErrorInfoLis]

    LogStep('laya更新ui文件')
    logEnum("########################################################")
    logEnum("########################################################")
    logEnum("########################################################")
    logEnum("如果有更新ui文件，请在ide重新发布，确保*DlgUI.as,.ts优先更新到")
    logEnum("之后回进行代码文件的替换")

    pass

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "d", ["debug"])
    for opt_name,opt_value in opts:
        if opt_name in ('-d','--debug'):
            debug = True

    start()
