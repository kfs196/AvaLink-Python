import numpy as np
import pandas as pd

from CoreLib.nodeClass import Node
from CoreLib.beamClass import Beam
from CoreLib.loadClass import (LoadForce,LoadMoment)


# Readfile类：用于读取模板数据并整理、规范化的工具箱 (Openpyxl重写)
class Readfile:

    # 初始化函数
    def __init__(self, dfList:list) -> None:

        # self.book = xl.load_workbook(xlBytes) # 从指定路径打开工作表
        self.NodeDict = self.readNodes(dfList[0]) # 从工作表中读取节点信息
        self.ElemDict = self.readElements(dfList[1],self.NodeDict) # 读取单元信息
        self.readNodalLoad(dfList[2],self.NodeDict,self.ElemDict) # 获得ForceDict及MomentDict两个属性

    
    # # 启动xlwings模块，使得打开工作表仅一次
    # def openXW(self) -> xw.Book:

    #     # 初始化xlwings模块，打开Excel表格
    #     app = xw.App(visible=True, add_book=False)
    #     app.display_alerts = False
    #     app.screen_updating = False # 以上为xlwings库的基本配置
    #     wb = app.books.open(r"template.xlsx")

    #     return wb


    # 读取节点类数据的功能函数，返回一个字典：
    def readNodes(self, wb:pd.DataFrame) -> dict:

        # 打开第一个工作簿，读取数据
        dfNode = pd.DataFrame(wb)
        rows = dfNode.shape[0] # 获取有效行数
        nodeDict = dict({}) # 创建一个空字典
        for rowi in range(rows): # 遍历每行，但应除去标题行
            nodeNum = len(nodeDict) # 获取点编号（自动排序）以计算自由度和ID
            if dfNode.iloc[rowi,2] is None: # 预先判断是否为空，增强程序稳定性
                pass
            else:
                tempNode = Node(dfNode.iloc[rowi,2],
                                dfNode.iloc[rowi,3],
                                dfNode.iloc[rowi,4],
                                nodeNum,
                                [dfNode.iloc[rowi,5], # 最后一个参数是反映节点约束情况的3*1列表
                                dfNode.iloc[rowi,6],
                                dfNode.iloc[rowi,7]]) # 创建一个Node对象
                nodeDict.update({dfNode.iloc[rowi,2] : tempNode}) # 将其加入字典，便于管理
        
        return nodeDict
    

    # 读取梁单元类数据的功能函数，返回一个字典：
    def readElements(self, wb:pd.DataFrame, nodeDict:dict) -> dict:

        # 打开第一个工作簿，读取数据
        dfElem = pd.DataFrame(wb)
        rows = dfElem.shape[0] # 获取有效行数
        elemDict = dict({}) # 创建一个空字典
        for rowi in range(rows): # 遍历每行，但应除去标题行
            elemNum = len(elemDict) # 获取单元编号（自动排序）以明确ID
            if nodeDict.get(dfElem.iloc[rowi,2]) is None: # 预先判断是否为空，同上
                pass
            else:
                tempElem = Beam(nodeDict[dfElem.iloc[rowi,2]], # 按照名称索引，从字典中取出Node
                                nodeDict[dfElem.iloc[rowi,3]],
                                dfElem.iloc[rowi,4],
                                dfElem.iloc[rowi,5],
                                dfElem.iloc[rowi,6],
                                elemNum,
                                [dfElem.iloc[rowi,7],
                                dfElem.iloc[rowi,8]])  # 创建一个Element对象
                elemDict.update({tempElem.name : tempElem}) # 将其加入字典，便于管理
            
        return elemDict
    

    # 读取集中荷载类数据的功能函数，返回一个字典：
    def readNodalLoad(self, wb:pd.DataFrame, nodeDict:dict, elemDict:dict) -> None:

        # 打开第一个工作簿，读取数据
        dfLoad = pd.DataFrame(wb)
        rows = dfLoad.shape[0] # 获取有效行数
        forceDict = dict({}) # 创建一个空字典：存储节点集中力
        momentDict = dict({}) # 创建一个空字典：存储杆端集中力偶

        for rowi in range(rows): # 遍历每行，但应除去提示行/标题行
            if 'F' in str(dfLoad.iloc[rowi,1]): ### 读取节点集中力，注意cell行列从1开始
                tempNode = nodeDict[str(dfLoad.iloc[rowi,2])]
                force =  LoadForce(tempNode,
                              dfLoad.iloc[rowi,3],
                              dfLoad.iloc[rowi,4])
                forceDict.update(force.loadDict)
                              
            elif 'M' in str(dfLoad.iloc[rowi,1]): ### 读取杆端集中力偶
                tempElem = elemDict[str(dfLoad.iloc[rowi,5])]
                moment = LoadMoment(tempElem,
                                    dfLoad.iloc[rowi,6],
                                    dfLoad.iloc[rowi,7],
                                    dfLoad.iloc[rowi,8],
                                    dfLoad.iloc[rowi,9])
                momentDict.update(moment.loadDict)
                
        self.ForceDict = forceDict
        self.MomentDict = momentDict # 直接在子函数中建立两个属性

