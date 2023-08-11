import numpy as np
import math
from CoreLib.nodeClass import Node


# Beam类：描述梁单元特征
class Beam:
    
    # 初始化函数
    def __init__(self, node1:Node, node2:Node, 
                 E:int, A:float, I:float, nElem:int, hinge:list) -> None: 

        # 基本特性
        self.ID = nElem # 杆件单元编号
        self.Pi = node1 # 杆端i节点
        self.Pj = node2 # 杆端j节点
        self.E = E # 杆件弹性模量
        self.A = A # 杆件截面面积
        self.I = I # 杆件抗弯惯性矩

        # 计算衍生特性
        self.name = str(node1.name+node2.name) # 杆件自动命名
        self.theta = self.__calTheta() # 计算杆件方位角
        self.length = self.__calLength() # 计算杆件长度
        # self.dofElem = (node1.dofDict).update(node2.dofDict) # 禁止！字典是引用类型变量！！！
        self.dofElem = {**node1.dofDict, **node2.dofDict} # 解耦、合并，得到梁单元位置编码及约束字典
        self.dofElemList = list(self.dofElem.keys()) # 仅存放梁单元位置编码向量，相对于上一个字典更方便操作
        self.hingeElem = self.__calHingeDict(hinge) # 反映杆件两端是否为铰接的字典

        # 矩阵特性:均初始化为零矩阵
        self.transMat = self.__calTransMat(self.theta) # 计算6*6转换矩阵
        self.kLocalMat = self.__calKLocal() # 单元坐标系刚度矩阵
        self.kGlobalMat = (self.transMat.T)@(self.kLocalMat)@(self.transMat)# 整体坐标系单元刚度矩阵
        
        self.dGlobalMat = np.zeros(6) # 整体坐标系下的位移矩阵 (在Structure类中填充)
        self.dLocalMat = np.zeros(6) # 局部坐标系下的位移矩阵 (在Structure类中填充)
        self.fLocalMat = np.zeros(6) # 局部坐标系下的外力矩阵 (在Structure类中填充)


    # 计算杆件相对于x轴正向的夹角的功能函数(私有成员)
    def __calTheta(self) -> float:

        if self.Pj.x == self.Pi.x: # 考虑恰为竖直90度的情况
            if self.Pj.y > self.Pi.y: # 区分竖杆的方向：向上/向下
                theta = math.pi/2 
            elif self.Pj.y < self.Pi.y:
                theta = -math.pi/2
        else:
            theta = math.atan2((self.Pj.y-self.Pi.y),(self.Pj.x-self.Pi.x))

        return theta # 弧度形式
    

    # 计算杆件长度的功能函数(私有成员)
    def __calLength(self) -> float:

        length = math.sqrt((self.Pj.y-self.Pi.y)**2+(self.Pj.x-self.Pi.x)**2)

        return length # 弧度形式
    

    # 计算并返回杆件两端铰接条件的功能函数（私有成员）
    def __calHingeDict(self, hingelist:list) -> dict:
        
        tempList = list([]) # 创建空数组便于赋值
        for item in hingelist:
            temp = True if item =='Y' else False
            tempList.append(temp)
        
        return dict({self.Pi.ID:tempList[0], 
                     self.Pj.ID:tempList[1]}) # 字典构成：杆端节点编号：是否铰接            
    
    
    # 形成6*6转换矩阵并将其返回的功能函数（私有成员）
    def __calTransMat(self,a:float) -> np.ndarray:

        mini = np.array([[math.cos(a),math.sin(a),0], # 先构造3*3小型转换矩阵
                              [-math.sin(a),math.cos(a),0],
                              [0,0,1]]) 
        zero3 = np.zeros((3,3),dtype=float) # 创建3*3零矩阵
        transMat = np.vstack((np.hstack((mini,zero3)),
                              np.hstack((zero3,mini)))) # 先横向拼接，再竖向拼接
        
        return transMat

    
    # 形成6*6单元刚度矩阵（单元局部坐标系）的功能函数（私有成员）
    def __calKLocal(self) -> np.ndarray :

        ia = (self.E*self.A) / (self.length) # 相对刚度：EA/l
        ii = (self.E*self.I) / (self.length) # 相对刚度：EI/l
        iidl = ii/(self.length) # EI/(l^2)
        iidll = iidl/(self.length) # EI/(l^3)
        klocal = np.array([[ia,0,0,-ia,0,0],
                           [0,12*iidll,6*iidl,0,-12*iidll,6*iidl],
                           [0,6*iidl,4*ii,0,-6*iidl,2*ii],
                           [-ia,0,0,ia,0,0],
                           [0,-12*iidll,-6*iidl,0,12*iidll,-6*iidl],
                           [0,6*iidl,2*ii,0,-6*iidl,4*ii]]) # 直接构造单元刚度矩阵
        
        return klocal
