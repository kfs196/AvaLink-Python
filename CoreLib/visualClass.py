import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from CoreLib.structureClass import Structure
from CoreLib.nodeClass import Node
from CoreLib.beamClass import Beam


# Visual类：根据计算结果，对结构位移、内力进行可视化的工具类
class Visual:

    # 初始化函数
    def __init__(self,elemDict:dict) -> None:

        self.elemDict = elemDict # 获取含有求解结果的单元字典    

        plt.rcParams['font.sans-serif'] = ['SimHei'] # 修改默认字体

    
    # 读取计算结果并生成杆端位移表格的功能函数
    def tableDeformed(self) -> pd.DataFrame:

        tempDict = dict({}) # 创建空字典便于管理与转换
        for key in self.elemDict.keys():
            item = self.elemDict[key]
            tempSer0 = pd.Series(item.dGlobalMat.tolist(), # 获取六个位移值，转换为Series
                                 index=['XI','YI','RI','XJ','YJ','RJ']) 
            tempSer1 = pd.Series([item.Pi.name,item.Pj.name],
                                 index=['PointI','PointJ'])
            tempSer = pd.concat([tempSer1,tempSer0],axis=0) # 竖向拼接两个Series
            tempDict.update({key : tempSer})
        
        return pd.DataFrame(tempDict).T
    
    
    # 读取计算结果并生成杆端内力表格的功能函数
    def tableForce(self) -> pd.DataFrame:

        tempDict = dict({}) # 创建空字典便于管理与转换
        for key in self.elemDict.keys():
            item = self.elemDict[key]
            tempSer0 = pd.Series(item.fLocalMat.tolist(), # 获取六个位移值，转换为Series
                                 index=['NI','QI','MI','NJ','QJ','MJ']) 
            tempSer1 = pd.Series([item.Pi.name,item.Pj.name],
                                 index=['PointI','PointJ'])
            tempSer = pd.concat([tempSer1,tempSer0],axis=0) # 竖向拼接两个Series
            tempDict.update({key : tempSer})
        
        return pd.DataFrame(tempDict).T
    
    
    # 自动计算视觉调整系数的功能函数
    # 计算思路：求解一个放大/缩小系数，使得最大偏移量与最大杆件长度比值为0.1~0.2左右
    def __calVersionParam(self, elemDict:dict, mode:int) -> float():

        maxLength = 0 # 先求解最大长度：常规的比较算法
        for key in elemDict.keys():
            if elemDict[key].length > maxLength:
                maxLength = elemDict[key].length

        tmpParamlist = list([]) # 再求解最大绘图参数(mode: [0变形，1轴力，2剪力，3弯矩])
        for key in elemDict.keys(): # 核心思路，将所有目标内力/位移取到一个数组中，然后查找最大值
            if mode == 0 : # 如果是线位移
                item = elemDict[key].dGlobalMat
                xyDisplace = list([item[0],item[1],item[3],item[4]]) # 取出所有线位移
                tmpParamlist.extend(np.abs(xyDisplace)) # 注意取绝对值和list.extend方法
            else : # 如果是轴力剪力弯矩
                item = elemDict[key].fLocalMat
                innerForce = list([item[mode-1],item[mode+2]]) # 取出杆件ij端同名力
                tmpParamlist.extend(np.abs(innerForce)/1000) # 力单位换算为kN
        maxParam = max(tmpParamlist) # 和maxLength求解思路不同，直接用标准库函数取最大值

        if mode == 0:
            return 0.07*maxLength/maxParam # 系数为尝试后看起来相对舒服的结果
        else:
            return 0.20*maxLength/maxParam       


    # 读取计算结果并绘制变形图的功能函数
    def plotDeformed(self) -> plt.Figure: # amp为视觉调整系数

        # 准备一：建立画布        
        fig,axe = plt.subplots()
        axe.set_aspect(1) # 设置等比例

        # 准备二： 计算自动绘图比例等
        amp = self.__calVersionParam(self.elemDict, 0)
        nodeText = dict({}) # 建立一个空字典以便于收集节点坐标信息并去重，方便标注
        elemLen = list([]) # 用于求解杆件长度，便于确定合适的标注偏移量

        for item in self.elemDict.values(): # 遍历每个单元/杆件，item为Beam类的对象

            # 第一步：绘制未变形的结构：灰色虚线
            MESHN = 21 # 控制绘图精度的常量
            xVector0 = np.linspace(item.Pi.x, item.Pj.x, MESHN) # 将x坐标线性插入19个点，共21个点
            yVector0 = np.linspace(item.Pi.y, item.Pj.y, MESHN) # 同上
            axe.plot(xVector0,yVector0,
                          linestyle='--', color='grey', linewidth=1)
            nodeText.update({item.Pi.name : (item.Pi.x,item.Pi.y)}) # 补充：将节点坐标信息添加入字典
            nodeText.update({item.Pj.name : (item.Pj.x,item.Pj.y)}) # 由于键的唯一性，能自动去重
            elemLen.append(item.length) # 获取杆件长度集合：辅助标注
            
            # 第二步：求解杆件的近似挠曲线
            # 思路：设挠曲线为三次方程，y = ax^3+bx^2+cx+d，利用位移和转角的边界条件解出待定系数
            # 四个边界条件对应四个方程组，可用矩阵表达并用numpy求解
            le = item.length # 获取杆件长度
            coeff = np.array([
                [0,0,0,1], # 代表：x=0时，y=y(i)
                [0,0,1,0], # 代表：x=0时，y'=theta(i)
                [le**3,le**2,le,1], # 代表：x=le时，y=y(j)
                [3*le**2,2*le,1,0]  # 代表：x=le时，y'=theta(j)
            ])
            dIJ = np.array([0,item.dLocalMat[2], # 策略：i端令纵向位移为0，j端取相对值
                            item.dLocalMat[4]-item.dLocalMat[1], # 表示yj相对于yi的位移量
                            item.dLocalMat[5]]).T # 转置为竖向
            pend = np.linalg.inv(coeff) @ dIJ # 解出待定系数向量：[a,b,c,d].T           

            # 第三步：将挠曲线计算结果用于杆件变形图的构建（插值）
            xVector = xVector0.copy() # 深拷贝（不共用内存，防止错误修改）
            yVector = yVector0.copy() # 同上
            shiftTemp = list([])
            for i in range(MESHN): # 其实总长度为上面设置的21
                li = np.sqrt((xVector0[i]-xVector0[0])**2 +
                             (yVector0[i]-yVector0[0])**2) # 计算从i端到当前位置的局部坐标距离
                shift = pend[0]*(li**3)+ pend[1]*(li**2)+ pend[2]*li+ pend[3] # 计算插值结果
                xVector[i] += amp*shift*(np.cos(item.theta+np.pi/2)) # 画图分析，确实需要加pi/2
                yVector[i] += amp*shift*(np.sin(item.theta+np.pi/2)) # x,y两向量即为杆件内插值结果
                shiftTemp.append(shift)

            # 第四步：叠加杆件内插值与杆端位移两部分，得总位移，绘图
            # 特别注意：xVector与yVector已经是整体坐标系下的数据了
            axe.plot(xVector+amp*item.dGlobalMat[0], # 以i端为基准，画j端
                          yVector+amp*item.dGlobalMat[1],
                          linestyle='-', color='teal', linewidth=1.2)
            
        axe.set_xlabel("Unit of lengt：m",fontsize=12) # 设置基本标注
        axe.set_ylabel("Unit of lengt：m",fontsize=12)
        axe.set_title("Deformation Diagram",fontsize=14)

        # 第五步：添加注释性标记 -> 结点名称标记
        meanLength = np.mean(elemLen)
        for key in nodeText.keys():
            axe.text(nodeText[key][0]-0.03*meanLength, # 策略：左上角偏移标注
                     nodeText[key][1]+0.01*meanLength,s=key,
                     fontdict={'fontsize': 12,'color':'steelblue'})

        return fig


    # 读取计算结果并绘制弯矩图的功能函数
    def plotMoment(self) -> plt.Figure:

        # 准备一：建立画布        
        fig,axe = plt.subplots()
        axe.set_aspect(1) # 设置等比例

        # 准备二： 计算自动绘图比例等
        amp = self.__calVersionParam(self.elemDict, 3)
        nodeText = dict({}) # 建立一个空字典以便于收集节点坐标信息并去重，方便标注
        elemLen = list([]) # 用于求解杆件长度，便于确定合适的标注偏移量

        MESHN = 21 # 控制绘图精度的常量
        for item in self.elemDict.values():
            # 特别注意，由于剪力规定绕隔离体顺时针为正，与“和y轴同正向”的局部坐标系有差异，应将j端反号
            # 举例：i端为正、j端为负，这时其实单元剪力为正值，因此应将j端反号才能画在上侧
            mi = Node('mi', item.Pi.x + item.fLocalMat[2]*np.cos(item.theta+np.pi/2) * amp/1000,
                      item.Pi.y + item.fLocalMat[2]*np.sin(item.theta+np.pi/2) * amp/1000,
                      -1, []) # 打一个绘图定位关键点以确定弯矩量值
            mj = Node('mj', item.Pj.x - item.fLocalMat[5]*np.cos(item.theta+np.pi/2) * amp/1000,
                      item.Pj.y - item.fLocalMat[5]*np.sin(item.theta+np.pi/2) * amp/1000,
                      -1, []) # 打一个绘图定位关键点
            axe.plot(np.linspace(item.Pi.x, item.Pj.x, MESHN), # 绘制原始框架
                        np.linspace(item.Pi.y, item.Pj.y, MESHN),
                        linestyle='-', color='grey', linewidth=1)
            axe.plot(np.linspace(mi.x, item.Pi.x, MESHN), # 绘制i端封闭线
                np.linspace(mi.y, item.Pi.y, MESHN),
                linestyle='-', color='teal', linewidth=1.2)
            axe.plot(np.linspace(mi.x, mj.x, MESHN), # 绘制i端封闭线
                    np.linspace(mi.y, mj.y, MESHN),
                    linestyle='-', color='teal', linewidth=1.2) # 绘制i-j弯矩变化线
            axe.plot(np.linspace(mj.x, item.Pj.x, MESHN), # 绘制i端封闭线
                    np.linspace(mj.y, item.Pj.y, MESHN),
                    linestyle='-', color='teal', linewidth=1.2) # 绘制i-j弯矩变化线

            nodeText.update({item.Pi.name : (item.Pi.x,item.Pi.y)}) # 补充：将节点坐标信息添加入字典
            nodeText.update({item.Pj.name : (item.Pj.x,item.Pj.y)}) # 由于键的唯一性，能自动去重
            elemLen.append(item.length) # 获取杆件长度集合：辅助标注

        axe.set_xlabel("Unit of lengt：m",fontsize=12)
        axe.set_ylabel("Unit of lengt：m",fontsize=12)
        axe.set_title("Bending Moment Diagram",fontsize=14)

        # 添加注释性标记 -> 结点名称标记
        meanLength = np.mean(elemLen)
        for key in nodeText.keys():
            axe.text(nodeText[key][0]-0.03*meanLength, # 策略：左上角偏移标注
                     nodeText[key][1]+0.01*meanLength,s=key,
                     fontdict={'fontsize': 12,'color':'steelblue'})

        return fig
    

    # 读取计算结果并绘制剪力图的功能函数
    def plotShear(self) -> plt.Figure:

        # 准备一：建立画布        
        fig,axe = plt.subplots()
        axe.set_aspect(1) # 设置等比例

        # 准备二： 计算自动绘图比例等
        amp = self.__calVersionParam(self.elemDict, 2)
        nodeText = dict({}) # 建立一个空字典以便于收集节点坐标信息并去重，方便标注
        elemLen = list([]) # 用于求解杆件长度，便于确定合适的标注偏移量

        MESHN = 21 # 控制绘图精度的常量
        for item in self.elemDict.values():
            # 特别注意，由于弯矩图画在受拉一侧，与“绕杆端逆时针为正”的局部坐标系有差异，应将j端反号
            # 举例：i端为负、j端为正，这时杆件下侧全部受拉，因此应将j端反号才能画在下侧
            qi = Node('qi', item.Pi.x + item.fLocalMat[1]*np.cos(item.theta+np.pi/2) * amp/1000,
                      item.Pi.y + item.fLocalMat[1]*np.sin(item.theta+np.pi/2) * amp/1000,
                      -1, []) # 打一个绘图定位关键点以确定弯矩量值
            qj = Node('qj', item.Pj.x - item.fLocalMat[4]*np.cos(item.theta+np.pi/2) * amp/1000,
                      item.Pj.y - item.fLocalMat[4]*np.sin(item.theta+np.pi/2) * amp/1000,
                      -1, []) # 打一个绘图定位关键点
            axe.plot(np.linspace(item.Pi.x, item.Pj.x, MESHN), # 绘制原始框架
                        np.linspace(item.Pi.y, item.Pj.y, MESHN),
                        linestyle='-', color='grey', linewidth=1)
            axe.plot(np.linspace(qi.x, item.Pi.x, MESHN), # 绘制i端封闭线
                np.linspace(qi.y, item.Pi.y, MESHN),
                linestyle='-', color='teal', linewidth=1.2)
            axe.plot(np.linspace(qi.x, qj.x, MESHN), # 绘制i-j弯矩变化线
                    np.linspace(qi.y, qj.y, MESHN),
                    linestyle='-', color='teal', linewidth=1.2) 
            axe.plot(np.linspace(qj.x, item.Pj.x, MESHN), # 绘制j端封闭线
                    np.linspace(qj.y, item.Pj.y, MESHN),
                    linestyle='-', color='teal', linewidth=1.2)

            nodeText.update({item.Pi.name : (item.Pi.x,item.Pi.y)}) # 补充：将节点坐标信息添加入字典
            nodeText.update({item.Pj.name : (item.Pj.x,item.Pj.y)}) # 由于键的唯一性，能自动去重
            elemLen.append(item.length) # 获取杆件长度集合：辅助标注

        axe.set_xlabel("Unit of lengt：m",fontsize=12)
        axe.set_ylabel("Unit of lengt：m",fontsize=12)
        axe.set_title("Shear Force Diagram",fontsize=14)

        # 添加注释性标记 -> 结点名称标记
        meanLength = np.mean(elemLen)
        for key in nodeText.keys():
            axe.text(nodeText[key][0]-0.03*meanLength, # 策略：左上角偏移标注
                     nodeText[key][1]+0.01**meanLength,s=key,
                     fontdict={'fontsize': 12,'color':'steelblue'})

        return fig

     
            
                