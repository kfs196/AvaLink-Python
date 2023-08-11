import streamlit as st
import pandas as pd
from CoreLib.readFileClass import Readfile
from CoreLib.visualClass import Visual


class StreamGUI:

    # 初始化函数
    def __init__(self) -> None:

        self.flag = 0 # 用于调试程序的辅助变量


    # 前处理(表格输入)基本页面的构建
    def setStartView(self) -> int and Readfile :

        st.title('AvaLink Streamlit Demo')
        st.markdown('这是一个利用Streamlit运行的Web小程序，用于求解简单的结构力学问题 (AvaLink-Python)')
        st.markdown('作者邮箱 :mailbox_closed: ：kfs196@126.com')
        st.divider()
        st.markdown('#### :star: 前处理部分：')
        st.markdown('##### 1.1. 编辑并上传模板表格')
        tableFile = st.file_uploader("请选择该表格文件上传，否则将无法完成计算：template.xlsx",
                                type=['xls','xlsx'], accept_multiple_files=False)

        if tableFile is not None:

            st.markdown('##### 1.2. 展示结构/荷载相关设置')

            df_node = pd.read_excel(tableFile,sheet_name='Nodes')
            st.markdown('###### :mag_right:该结构的:blue[节点]信息如下：')
            st.dataframe(df_node)

            df_elem = pd.read_excel(tableFile,sheet_name='Elements')
            st.markdown('###### :mag_right:该结构的:blue[单元]信息如下：')
            st.dataframe(df_elem)

            df_load = pd.read_excel(tableFile,sheet_name='NodalLoad',header=1) # 跳过第一行
            st.markdown('###### :mag_right:该结构的:blue[外荷载]信息如下：')
            st.dataframe(df_load)
            st.markdown('请认真检查上述信息是否准确，若有误则重新修改模板上传；若无误则提交计算')

            st.markdown('##### 1.3. 提交计算')
            st.markdown('确认无误并点击按钮提交计算后，将自动进入后处理结果展示：')
            

            if st.button(label='提交计算',help='点击后将自动计算，若成功则返回后处理结果'):

                try: # try-except-finally异常处理，用于用户非法输入的提示
                    readfile = Readfile(list([df_node,df_elem,df_load])) # 开始读取数据
                    self.flag += 1
                except :
                    st.warning('ValueError: 表格中有不合理的数据输入，请检查后重新上传！')
                    return None 
                else:
                    return readfile           
                
        else:
            return None # 如果走了这一分支，主程序将不再进行 (见Program.py)
        

    # 后处理(表格结果展示)基本页面的构建
    def setPostGrid(self, vis:Visual) -> None:

        pd.set_option('display.precision', 6)
        st.divider()
        st.markdown('#### :star: 后处理部分：')

        st.markdown('##### 2.1. 展示计算结果表格')
        st.markdown('###### :mag_right:该结构的:blue[单元位移]数据如下：(双击单元格查看高精度值)')
        st.dataframe(vis.tableDeformed()) # 获取杆单元在整体坐标系下位移的数值
        st.markdown('###### :mag_right:该结构的:blue[单元内力]数据如下：(双击单元格查看高精度值)')
        st.dataframe(vis.tableForce()) # 获取杆单元在整体坐标系下位移的数值
        self.flag += 1

    # 后处理(图形结果展示)基本页面的构建
    def setPostGraph(self, vis:Visual) -> None:

        st.markdown('##### 2.2. 展示变形与内力图表')
        st.markdown('###### :mag_right:该结构的:blue[变形图]如下：')
        st.pyplot(vis.plotDeformed(),use_container_width=True) # 使用默认宽度画图（待优化）
        st.markdown('###### :mag_right:该结构的:blue[弯矩图]如下：')
        st.pyplot(vis.plotMoment(),use_container_width=True)
        st.markdown('###### :mag_right:该结构的:blue[剪力图]如下：')
        st.pyplot(vis.plotShear(),use_container_width=True)





        