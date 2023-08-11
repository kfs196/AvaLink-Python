# import


# Node类：用于描述节点的基本属性
class Node:

    # 初始化函数
    def __init__(self, name:str,x:float, y:float, 
                  nNode:int, dofStr:list) -> None:
        self.name = name # 描述节点名称
        self.ID = nNode # 描述自动生成的节点编号
        self.x = x # 描述节点平面x坐标
        self.y = y # 描述节点平面y坐标
        self.dofDict = self.__dofStringConverter(nNode,dofStr) # 表示节点自由度约束情况


    # 将约束信息字符串转换为约束自由度字典的功能函数(私有成员)
    def __dofStringConverter(self,nNode:int, dofStr:list) -> dict:

        dofDict = dict({}) # 创建一个字典组便于填充
        if nNode == -1:
            return dofDict # 对于某些非节点的辅助点，不需要自由度等属性，直接返回空字典

        dofIndex = list([3*nNode,3*nNode+1,3*nNode+2]) # 确定每节点的三个位移自由度编号
        for i,num in enumerate(dofIndex):
            temp = True if dofStr[i]=='Y' else False
            dofDict.update({num:temp}) # 键值对格式 -> 自由度编号：约束情况

        return dofDict



