import done_deserialize from "./deserialize_help";

const { ccclass, property } = cc._decorator;

@ccclass
export default class CommI18nHelper extends cc.Component {
    private _child = null;
    constructor() {
        super()
    }
    setChild(child) {
        this._child = child
    }
    _deserialize(content, self) {
        if (this._child == null) {
            console.error('CommI18nHelper::请调用 setChild 设置脚本节点')
            return
        }
        return done_deserialize(self, this._child)
    }
}
