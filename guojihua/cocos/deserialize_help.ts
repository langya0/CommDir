var IDENTIFIER_RE = /^[$A-Za-z_][0-9A-Za-z_$]*$/;

var tmpValueDesc = {
    value: undefined,
    enumerable: false,
    writable: false,
    configurable: true
}

function value(obj, prop, value, writable, enumerable) {
    tmpValueDesc.value = value;
    tmpValueDesc.writable = writable;
    tmpValueDesc.enumerable = enumerable;
    Object.defineProperty(obj, prop, tmpValueDesc);
    tmpValueDesc.value = undefined;
}

function getDefault(defaultVal) {
    if (typeof defaultVal === 'function') {
        if (CC_EDITOR) {
            try {
                return defaultVal();
            }
            catch (e) {
                return undefined;
            }
        }
        else {
            return defaultVal();
        }
    }
    return defaultVal;
}

function getClassName(objOrCtor) {
    if (typeof objOrCtor === 'function') {
        var prototype = objOrCtor.prototype;
        if (prototype && prototype.hasOwnProperty('__classname__') && prototype.__classname__) {
            return prototype.__classname__;
        }
        var retval = '';
        //  for browsers which have name property in the constructor of the object, such as chrome
        if (objOrCtor.name) {
            retval = objOrCtor.name;
        }
        if (objOrCtor.toString) {
            var arr, str = objOrCtor.toString();
            if (str.charAt(0) === '[') {
                // str is "[object objectClass]"
                arr = str.match(/\[\w+\s*(\w+)\]/);
            }
            else {
                // str is function objectClass () {} for IE Firefox
                arr = str.match(/function\s*(\w+)/);
            }
            if (arr && arr.length === 2) {
                retval = arr[1];
            }
        }
        return retval !== 'Object' ? retval : '';
    }
    else if (objOrCtor && objOrCtor.constructor) {
        return getClassName(objOrCtor.constructor);
    }
    return '';
}


function compileObjectType(sources, defaultValue, accessorToSet, propNameLiteralToSet, assumeHavePropIfIsValue) {
    if (defaultValue instanceof cc.ValueType) {
        // fast case
        if (!assumeHavePropIfIsValue) {
            sources.push('if(prop){');
        }
        var ctorCode = getClassName(defaultValue);
        sources.push(`s._deserializeTypedObject(o${accessorToSet},prop,${ctorCode});`);
        if (!assumeHavePropIfIsValue) {
            sources.push('}else o' + accessorToSet + '=null;');
        }
    }
    else {
        sources.push('if(prop){');
        if (CC_EDITOR || CC_TEST) {
            sources.push('s._deserializeObjField(o,prop,' + propNameLiteralToSet + ',t&&o);');
        }
        else {
            sources.push('s._deserializeObjField(o,prop,' + propNameLiteralToSet + ');');
        }
        sources.push('}else o' + accessorToSet + '=null;');
    }
}

function escapeForJS(s) {
    return JSON.stringify(s).
        // see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify
        replace(/\u2028/g, '\\u2028').
        replace(/\u2029/g, '\\u2029');
}

function compileDeserialize(self, klass) {
    var TYPE = '$_$' + 'type';
    var RAW_TYPE = '$_$' + 'rawType';
    var EDITOR_ONLY = '$_$' + 'editorOnly';
    var SERIALIZABLE = '$_$' + 'serializable';
    var DEFAULT = '$_$' + 'default';
    var SAVE_URL_AS_ASSET = '$_$' + 'saveUrlAsAsset';
    var FORMERLY_SERIALIZED_AS = '$_$' + 'formerlySerializedAs';

    /// 获取 __attrs__
    var attrs = {}//Attr.getClassAttrs(klass);

    var props = klass.__props__;
    // self, obj, serializedData, klass, target
    var sources = [
        'var prop;'
    ];
    var fastMode = false
    // sources.push('var vb,vn,vs,vo,vu,vf;');    // boolean, number, string, object, undefined, function
    for (var p = 0; p < props.length; p++) {
        var propName = props[p];
        var propNameLiteralToSet;
        var rawType = attrs[propName + RAW_TYPE];
        if (!rawType) {
            if ((CC_PREVIEW || (CC_EDITOR && self._ignoreEditorOnly)) && attrs[propName + EDITOR_ONLY]) {
                var mayUsedInPersistRoot = (propName === '_id' && cc.isChildClassOf(klass, cc.Node));
                if (!mayUsedInPersistRoot) {
                    continue;   // skip editor only if in preview
                }
            }
            if (attrs[propName + SERIALIZABLE] === false) {
                continue;   // skip nonSerialized
            }

            var accessorToSet;
            if (IDENTIFIER_RE.test(propName)) {
                propNameLiteralToSet = '"' + propName + '"';
                accessorToSet = '.' + propName;
            }
            else {
                propNameLiteralToSet = escapeForJS(propName);
                accessorToSet = '[' + propNameLiteralToSet + ']';
            }

            var accessorToGet = accessorToSet;
            if (attrs[propName + FORMERLY_SERIALIZED_AS]) {
                var propNameToRead = attrs[propName + FORMERLY_SERIALIZED_AS];
                if (IDENTIFIER_RE.test(propNameToRead)) {
                    accessorToGet = '.' + propNameToRead;
                }
                else {
                    accessorToGet = '[' + escapeForJS(propNameToRead) + ']';
                }
            }

            sources.push('prop=d' + accessorToGet + ';');
            sources.push(`if(typeof ${CC_JSB ? '(prop)' : 'prop'}!=="undefined"){`);

            // function undefined object(null) string boolean number
            var defaultValue = getDefault(attrs[propName + DEFAULT]);
            if (fastMode) {
                var isPrimitiveType;
                var userType = attrs[propName + TYPE];
                if (defaultValue === undefined && userType) {
                    isPrimitiveType = userType === cc.String ||
                        userType === cc.Integer ||
                        userType === cc.Float ||
                        userType === cc.Boolean;
                }
                else {
                    var defaultType = typeof defaultValue;
                    isPrimitiveType = (defaultType === 'string' && !attrs[propName + SAVE_URL_AS_ASSET]) ||
                        defaultType === 'number' ||
                        defaultType === 'boolean';
                }

                if (isPrimitiveType) {
                    sources.push(`o${accessorToSet}=prop;`);
                }
                else {
                    compileObjectType(sources, defaultValue, accessorToSet, propNameLiteralToSet, true);
                }
            }
            else {
                sources.push(`if(typeof ${CC_JSB ? '(prop)' : 'prop'}!=="object"){` +
                    'o' + accessorToSet + '=prop;' +
                    '}else{');
                compileObjectType(sources, defaultValue, accessorToSet, propNameLiteralToSet, false);
                sources.push('}');
            }
            sources.push('}');
        }
        else {
            if (IDENTIFIER_RE.test(propName)) {
                propNameLiteralToSet = '"' + propName + '"';
            }
            else {
                propNameLiteralToSet = escapeForJS(propName);
            }
            // always load raw objects even if property not serialized
            // 这里假定每个asset都有uuid，每个json只能包含一个asset，只能包含一个rawProp
            sources.push('if(s.result.rawProp)\n' +
                'cc.error("not support multi raw object in a file");');
            sources.push('s.result.rawProp=' + propNameLiteralToSet + ';');
        }
    }
    if (props[props.length - 1] === '_$erialized') {
        // deep copy original serialized data
        sources.push('o._$erialized=JSON.parse(JSON.stringify(d));');
        // parse the serialized data as primitive javascript object, so its __id__ will be dereferenced
        sources.push('s._deserializePrimitiveObject(o._$erialized,d);');
    }
    return Function('s', 'o', 'd', 'k', 't', sources.join(''));
}

/**
 * 获取当前语言，可重写
 */
function getlang() {
    if (!window.location) return {};
    var q = window.location.search || window.location.hash;
    if (q) {
        var pairs = q.substring(1).split("&");
        var obj = {};
        for (var i = 0; i < pairs.length; i++) {
            obj[pairs[i].split("=")[0]] = pairs[i].split("=")[1];
        }
        return obj['lang']
    }
    return "";
}

/**
 * 
 * @param obj deserialize 原始节点
 */
function befDeserialize(obj) {
    var len = obj.result.uuidList.length;
    var curL = getlang()
    var lan_uuid = {}
    for (var i = 0; i < len; ++i) {
        if (obj.result.uuidObjList[i]['language'] && obj.result.uuidObjList[i]['language']) {
            if (!lan_uuid[obj.result.uuidObjList[i]['language']])
                lan_uuid[obj.result.uuidObjList[i]['language']] = []
            lan_uuid[obj.result.uuidObjList[i]['language']].push(obj.result.uuidList[i])
        }
    }
    var getIndex = (uuid) => {
        for (var x in lan_uuid) {
            for (var i = 0; i < lan_uuid[x].length; ++i) {
                if (lan_uuid[x][i] == uuid) {
                    return i
                }
            }
        }
        return -1;
    }

    for (var i = 0; i < len; ++i) {
        var index = getIndex(obj.result.uuidList[i])
        if (index != -1) {
            if (CC_EDITOR || CC_TEST) {
            } else {
                obj.result.uuidList[i] = lan_uuid[curL][index]
            }
        }
    }
}

/**
 * @param self 原始数据
 * @param klass 脚本类
 */
export default function done_deserialize(self, klass) {
    /// 前置优化处理
    befDeserialize(self)

    // 拿到当前脚本序列化信息
    var serialized;
    for (var i = 0; i < self.customEnv.content.length; ++i) {
        if (self.customEnv.content[i].__type__ == klass.__proto__.__cid__) {
            serialized = self.customEnv.content[i]
        }
    }

    /// deserialize.js 翻译执行
    var deserialize = compileDeserialize(self, klass.__proto__.constructor)
    deserialize(self, klass, serialized, klass.__proto__.constructor, undefined);
    return klass
}
