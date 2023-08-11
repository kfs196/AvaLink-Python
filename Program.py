from GUI.streamClass import StreamGUI
from CoreLib.structureClass import Structure
from CoreLib.visualClass import Visual


# 主程序模块
# UI框架：利用Streamlit完成Web可视化功能
if __name__ == '__main__':

    stream = StreamGUI() # 初始化UI界面并进行交互
    structureFile = stream.setStartView()

    if (structureFile is not None) :
        force0 = structureFile.ForceDict # 节点集中力
        moment0 = structureFile.MomentDict # 杆端集中力偶
        frame = Structure(structureFile,force0,moment0) # 初始化结构类，组装单元刚度矩阵与外力
        kMatrix = frame.integKGlobal # 原始刚度矩阵（整体坐标系）
        fVector = frame.loadVector # 原始节点力向量（整体坐标系）
        boundary = frame.bc # 边界条件约束向量
        distPrimary = Structure.solver(kMatrix, fVector, boundary) # 求解
        Structure.elememtPost(distPrimary,structureFile.ElemDict) # 后处理，将结果返回给杆单元

        visPost = Visual(structureFile.ElemDict) # 初始化可视化类 
        stream.setPostGrid(visPost) # 展示表格数据
        stream.setPostGraph(visPost) # 展示图形数据（剪力图弯矩图变形图）








    


