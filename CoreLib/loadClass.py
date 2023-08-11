from CoreLib.nodeClass import Node
from CoreLib.beamClass import Beam
import math


# LoadForce类：处理作用于节点的集中力(F)
class LoadForce:
    
    # 初始化函数：用于接收F类型的荷载
    def __init__(self, targetN:Node, force0:float, angleDegree:float) -> None:                   
        
        self.loadDict = self.__calForceDict(targetN,force0,angleDegree)    


    # 对集中力按整体坐标系方向进行分解返回字典的功能函数(私有成员)
    def __calForceDict(self, target:Node, force0:float, 
                       angleDegree:float) -> dict:
                        
        fx = force0*math.cos(angleDegree*(math.pi)/180) # 投影分解，注意转换为弧度
        fy = force0*math.sin(angleDegree*(math.pi)/180) 
        forceDict=dict({}) # 创建一个空字典用于存放整体坐标系节点荷载
        templist = [fx,fy,0]
        i = 0
        for key in target.dofDict.keys(): # 这里直接取用Node对象的结点位移自由度编号
            forceDict.update({key:templist[i]}) # 目的：一一对应填充
            i += 1

        return forceDict 
   


# LoadMoment类：处理作用于杆端的集中力偶(M)
class LoadMoment:
    
    # 初始化函数：用于接收M类型的荷载
    def __init__(self, targetE:Beam, 
                 mi:float, rdi:str, mj:float, rdj:str) -> None:
        
        self.loadDict = self.__calMomentDict(targetE,[mi,mj],[rdi,rdj])

    
    # 对集中力偶进行整理的功能函数(私有成员)
    def __calMomentDict(self,targetE:Beam, mList:float, rdList:str) -> dict:
        
      signList = [1 if i=='L' else -1 if i=='R' else 0 for i in rdList] # if-else的推导式写法
      momentDict=dict({}) # 创建一个空字典用于存放整体坐标系杆端力偶
      for k in range(2): # k取值0/1，用于表征杆件的i端与j端
          # key的构成是双元素元组：杆件编号+弯矩位移编号(3*k+2 恰好是6个位移中的弯矩)
          key = tuple((targetE.ID,targetE.dofElemList[3*k+2])) # 元组为值类型，可用作字典key
          momentDict.update({key : mList[k]*signList[k]}) # 以双元素元组为key，是防止铰接的情况
          
      return momentDict
            

