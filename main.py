from CoreLib.readFileClass import Readfile
from CoreLib.structureClass import Structure
from CoreLib.visualClass import Visual
import numpy as np
import pandas as pd
import openpyxl as xl


# 主程序模块
if __name__ == '__main__':

    # readfile = Readfile() # 初始化前处理模块，并读取模板数据
    # force0 = readfile.ForceDict # 节点集中力
    # moment0 = readfile.MomentDict # 杆端集中力偶

    # frame = Structure(readfile,force0,moment0) # 初始化结构类，组装单元刚度矩阵与外力

    # kMatrix = frame.integKGlobal # 原始刚度矩阵（整体坐标系）
    # fVector = frame.loadVector # 原始节点力向量（整体坐标系）
    # boundary = frame.bc # 边界条件约束向量
    # distPrimary = Structure.solver(kMatrix, fVector, boundary) # 求解
    # Structure.elememtPost(distPrimary,readfile.ElemDict) # 后处理，将结果返回给杆单元

    # vis = Visual(readfile.ElemDict) # 初始化可视化类
    # vis.plotDeformed(500) # 绘制变形图
    # vis.plotMoment(0.2) # 绘制弯矩图
    # vis.showfig() # 展示图表
    
    # *************

    # wb = xl.load_workbook('template.xlsx')
    # sheet = wb['Nodes']
    # print(sheet.cell(2,2).value)

    # Series1 = pd.Series([1,2,3,4],index=['a','b','c','d'])
    # Series2 = pd.Series(['Aa','Bb'],index=['x','y'])
    # print(pd.concat([Series2,Series1],axis=0))
    
    list1 = list([1,-2,3,-4,5])
    print(np.mean(np.abs(list1)/10))



    pass