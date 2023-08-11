import numpy as np
from CoreLib.nodeClass import Node
from CoreLib.beamClass import Beam
from CoreLib.readFileClass import Readfile


# Structure类：用于表达将节点、单元与荷载集成后的分析模型 (后处理法)
class Structure:

    # 初始化函数
    def __init__(self, structFile:Readfile, force0:dict, moment0:dict) -> None:
       
       self.structFile = structFile # 读取表格基本数据
       self.bc = self.__integBoundarys(structFile.NodeDict) # 描述边界条件的字典
       self.changeLog = list([]) # 用于记录铰接引起位移号码变化的列表，内为元组：(初始编号,变化后编号)
       self.extNodeCount = self.__hingeProcess(structFile.ElemDict) # 描述铰接节点附加位移的字典
       self.integKGlobal = self.__makeIntegPrimary(self.bc,structFile.ElemDict,
                                                   self.extNodeCount, self.changeLog) # 集成原始整体刚度矩阵
       self.loadVector = self.__calLoadVector(force0, moment0, 
                                              self.extNodeCount,self.changeLog)


    # 用于集成Node类中所含约束条件的功能函数(私有成员)
    def __integBoundarys(self, nodeDict:dict) -> dict:
       
       boundaryDict = dict({}) # 创建一个空字典，用于存储边界条件合集
       for item in list(nodeDict.values()):
          boundaryDict.update(item.dofDict)

       return boundaryDict
    
   
    # 处理/管理铰节点编号的功能函数
    def __hingeProcess(self, elemDict:dict) -> dict:
       
       isHingeList = list([]) # 空数组，存放满足铰接条件的节点编号
       for outer in elemDict.values(): # outer是一个Beam对象
          for inner in outer.hingeElem: # inner是一个Beam对象其属性：hingeElem字典，的键
             if outer.hingeElem[inner] == True:
                isHingeList.append([inner,outer.ID]) # 接下来，在这个list中筛选非支座铰节点
       # 辅助说明：nodeCount字典结构: {nodeID(int) : [count(int),elem1(int),elem2(int)…]}
       nodeCount = dict({}) # 创建字典便于对isHingeList中节点出现数目进行统计
       for kl in isHingeList:  # 功能：nodeCount字典中查找了isHingeList中X节点出现n次
          key0 = kl[0]
          if key0 in nodeCount.keys():
             (nodeCount[key0])[0] += 1 # 辅助理解：kl为2元素列表，k[0]其实是含铰节点编号
             nodeCount[key0].append(kl[1]) # 字典值列表增加一个元素（杆件编号）
          else:
             nodeCount[key0] = [1,kl[1]] # 建立二维列表，存放出现次数与相应杆单元编号
       for kl in isHingeList: # 筛选：节点存在铰支座且仅在isHingeList中出现一次，这时不增加位移数目
          key0 = kl[0]
          if (nodeCount[key0])[0] == 1: # 满足此条件，说明仅出现一次
            if ((self.bc[3*key0]==True or self.bc[3*key0+1]==True) and
               self.bc[3*key0+2]==False):  # 满足这三个条件，说明该点处存在固定/滑动铰支座约束
               if key0 in nodeCount: # 增强稳定性，其实可不用
                  del nodeCount[key0] # 同时满足上面1+3个条件则删除字典中的键值对
       for k in nodeCount.keys():
          (nodeCount[k])[0] -= 1 # 自减1后，得到了对于该节点的铰接附加位移数目
       
       return nodeCount


    # 用于集成结构的总体原始刚度矩阵的功能函数【核心】
    def __makeIntegPrimary(self, bc:dict, elemDict:dict, 
                           nodeCount:dict, log:list) -> np.ndarray:
       
       # 第一步，计算铰接影响附加位移数目
       extDisplaceCount = 0
       for k in nodeCount.keys():
          extDisplaceCount += (nodeCount[k])[0] # 统计整个结构的附加位移数目
       matNum = len(self.bc) + extDisplaceCount # 这就是考虑铰接影响的结构总位移数量

       ### 第二步：根据铰接影响字典nodeCount，增加杆端转角位移编号
       for k in nodeCount.keys(): # k 为节点编号
          for bn in nodeCount[k][2:] : # 此时循环的范围是第二个及以后的杆件（第一杆件不需要附加位移编号）
             for beam in elemDict.values(): # 此循环：按ID查找杆件
                if beam.ID == bn:  
                   indexBeam = beam.dofElemList.index(3*k+2) # 锁定杆端该节点的转角位移编号
                   beam.dofElemList[indexBeam] = len(self.bc) # 相当于拓展一个新变换，原编号最大等于等式右端-1
                   bc.update({beam.dofElemList[indexBeam]:False}) #注意，beam.dofElem字典并未更新
                   log.append([3*k+2,beam.dofElemList[indexBeam]]) # 在日志列表中写入一个列表，描述变化
     
       ### 第三步：由beam.dofElemList为参考组建结构的原始刚度矩阵
       integPrimary = np.zeros((matNum,matNum),dtype=float) # 创建空矩阵
       for beam in elemDict.values():
          pos = beam.dofElemList # pos即代表单元定位向量 
          for i in range(6): # beam 单元刚度矩阵大小总是6*6
             for j in range(6): # i,j 代表行列索引
                posi = pos[i]
                posj = pos[j] # 将矩阵编号转换为单元定位向量中的"位置码"
                integPrimary[posi,posj] += beam.kGlobalMat[i,j] # 实现刚度矩阵组建，对号入座

       return integPrimary


    # 用于集成集中力、力偶为节点外力向量的功能函数【核心】
    def __calLoadVector(self, forceDict:dict, momemtDict:dict, 
                        nodeCount:dict, log:list) ->np.ndarray:
       
       # 第一步，计算铰接影响附加位移数目，建立空向量(注意self.bc已被上一函数修改)
       vecNum = len(self.bc) # 这就是考虑铰接影响的结构总位移数量
       loadVector = np.zeros(vecNum,dtype=int) # 一维水平0向量，用于后续添加外力
       
       # 第二步，将节点集中力荷载添加到外力向量中
       for fk in forceDict.keys():
          loadVector[fk] += forceDict[fk]

       # 第三步，将杆端集中力偶荷载转化，并添加到外力向量中
       column0 = [row[0] for row in log] # 二维列表取出第一列（更改之前的节点）
       for mk in list(momemtDict.keys()): # 注意mk是一系列的元组：(杆件编号，位移编号)
          for hinge in nodeCount.values(): # hinge是nodeCount字典的值，一系列的列表
             if (mk[0] in hinge[2::]) and (mk[1] in column0): # 如果涉及到了需要增加编号的力偶
                for item in log: # item是元组（变化前编号，变化后编号）
                   if mk[1] == item[0]: # mk中的位移编号为未变化位移编号，因此需要转换为已变化编号
                      loadVector[item[1]] += momemtDict[mk]
             else:
                loadVector[mk[1]] += momemtDict[mk]

       return loadVector


    # 用于综合边界条件与外荷载，并完成求解的静态函数【核心】
    @ staticmethod
    def solver(kGlobal:np.ndarray, fGlobal:np.ndarray, bc:dict) -> np.ndarray:   
       
       # 第一步：利用置大数法，改写原始刚度方程
       BIGN = 10**30 # 定义一个足够大的数,如10^30
       kPGlobal = kGlobal.copy() # 深拷贝一份，内存分配不同，不会“改一处而全变”
       fPGlobal = fGlobal.copy() # 深拷贝一份，同上
       for i in bc.keys():
          if bc[i] == True: # 如果恰是被约束的位移条件：
             kPGlobal[i,i] = BIGN # 置大数法，这样相当于解出该处位移为0，从而近似设置边界条件
             fPGlobal[i] = 0 # 其实是 BIGN*0

       # 第二步：利用Numpy线性代数模块求解矩阵方程
       displace = np.linalg.solve(kPGlobal,fPGlobal)

       return displace
    
    
    # 用于将结果回传给各个杆件单元，并计算出局部坐标系杆端力的静态方法【关键】
    @ staticmethod
    def elememtPost(displace:np.ndarray, elemDict:dict) -> None:
       for item in elemDict.values():
          item.dGlobalMat = displace[np.array(item.dofElemList)] # numpy 整型数组为索引
          item.dLocalMat = (item.transMat) @ (item.dGlobalMat) # 计算局部坐标系下的位移向量
          item.fLocalMat = (item.kLocalMat) @ (item.dLocalMat) # 计算局部坐标系下的杆端力



             
             
                   
      #  for k in nodeCount.keys(): # 目标：由铰接节点查询出
      #     for beam in elemDict.keys():
      #        if elemDict[beam]
          

             
      #  return nodeCount
             
             
             
          
       
               
                
       
