# %%
# Author: Yini Xiao 生信2001肖旖旎 2020317210123; Date: 2022-12-27;
# 项目简介：基于GUI的蛋白质序列分析工具
# 参考代码：https://github.com/PySimpleGUI/PySimpleGUI

import PySimpleGUI as sg
import os
from Bio import SeqIO
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import pylab
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
from urllib.request import urlopen
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from time import sleep


#读取标准fasta文件(允许读取多序列)
def open_file():
    filename = sg.popup_get_file('Enter the sequences you wish to process')
    sg.popup('You entered is finished', filename)
    return filename


#设计Multiline的复制粘贴剪切输入
right_click_menu = ['', ['Copy', 'Paste', 'Cut', 'Select All']]
def multline_operate(button, window, element):
    if button == 'Copy':
            text = element.Widget.selection_get()
            window.TKroot.clipboard_clear()
            window.TKroot.clipboard_append(text)
    elif button == 'Paste':
        element.Widget.insert(sg.tk.INSERT, window.TKroot.clipboard_get())
    elif button == 'Cut':
            text = element.Widget.selection_get()
            window.TKroot.clipboard_clear()
            window.TKroot.clipboard_append(text)
            element.update('')
    elif button == 'Select All':
        element.Widget.selection_clear()
        element.Widget.tag_add('sel', '1.0', 'end')


#读取用户输入的序列并存储
def input_file(submit):
    oflname = './temp.fa'
    ofl = open(oflname, 'wt') #open file in a writing and text model
    ostr = submit
    ofl.write(ostr)
    ofl.close() #please check the file D:\frq.txt to see what you got
    return oflname

    
#返回所有序列的ID
def seq_ID(filename):
    ID = ''
    for seq in SeqIO.parse(filename, 'fasta'):
        temp = seq.id
        ID = ID + '\n' + temp 
    sg.popup('You sequences ID is :', ID)

#返回所有序列的长度
def seq_len(filename):
    seq_len = ''
    for seq in SeqIO.parse(filename, 'fasta'):
        temp = '{} : {}'.format(seq.id,len(seq))
        seq_len = seq_len + '\n' + temp
    sg.popup('You sequences Length is :', seq_len)


#返回所有序列的相对分子量
def seq_weight(filename):
    seq_weight = ''
    for seq in SeqIO.parse(filename, 'fasta'):
        #调用biopython中ProteinAnalysis进行运算
        analyzed_seq = ProteinAnalysis(str(seq.seq))
        temp = '{} : {}'.format(seq.id,analyzed_seq.molecular_weight())
        seq_weight = seq_weight + '\n' + temp
    sg.popup('You sequences weight is :', seq_weight)


#基于 Hydropath. / Kyte & Doolittle 的疏水性定义
kd = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5,
"Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
"L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6,
"S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}

#绘制疏水性曲线函数
def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


#返回蛋白质的疏水性曲线可视化曲线
def seq_hydrophobicity(filename):
    for seq in SeqIO.parse(filename, "fasta"):
        seq_kd = []
        pylab.subplots(figsize=(6, 2), dpi=100)
        for n in seq:
            seq_kd.append(kd[n])
            plt.title("{} hydrophobicity (Hydropath. / Kyte & Doolittle)".format(seq.id))
            pylab.plot(seq_kd)
            plt.xlabel("position")
            plt.ylabel("scores")

        fig = pylab.gcf()
        figure_x, figure_y, figure_w, figure_h = fig.bbox.bounds

        layout = [[sg.Text('Hydrophobicity', font='Any 18')],
            [sg.Canvas(size=(figure_w, figure_h), key='canvas')],
            [sg.OK(pad=((figure_w / 2, 0), 3), size=(4, 2))]]

        window = sg.Window('Hydrophobicity analysis results',
                    layout, finalize=True)
        fig_canvas_agg = draw_figure(window['canvas'].TKCanvas, fig)

    event, values = window.read()
    window.close()


#返回所有序列的氨基酸频率
def aa_freq(filename):
    aa_freq = ''
    i = 0
    for seq in SeqIO.parse(filename, 'fasta'):
        aa_dic = {'G': 0, 'A': 0, 'V': 0, 'L': 0, 'I': 0, 'P': 0, 'F': 0, 'Y': 0,\
        'W': 0, 'S': 0, 'T': 0, 'C': 0, 'M': 0, 'N': 0, 'Q': 0, 'D': 0, 'E': 0,\
        'K': 0, 'R': 0, 'H': 0} #建立氨基酸数量dict
        for n in seq:
                i += 1
                aa_dic[n] += 1
        #计算氨基酸频率
        aa_dic = {k: round(v / total, 4) for total in (sum(aa_dic.values()),) for k, v in aa_dic.items()}
        temp = '{} : {}'.format(seq.id,aa_dic) 
        aa_freq = aa_freq + '\n' + temp
    sg.popup_scrolled('You sequences amino acid frequency is :', aa_freq,size=(150, 30))





#使用WoLF PSORT进行亚细胞定位爬虫
def sub_local(filename):
    url="https://wolfpsort.hgc.jp/"
    for ProSeq in SeqIO.parse(filename, "fasta"):

        #用户需输入亚细胞定位所需的organism_type
        layout =  [[sg.Text('Please input the organism_type of {}'.format(ProSeq.id))], 
                [sg.ReadButton('Animal', size = (15,1)),sg.ReadButton('Plant', size = (15,1)),sg.ReadButton('Fungi', size = (15,1))]]
        window = sg.Window('Organism type', layout)
        while True:
            button, value = window.Read()
            if button is not None:  
                if button == 'Animal':
                    type = 0
                    sg.popup('{} organism_type is animal, please wait for a while.'.format(ProSeq.id))
                    window.close() 
                if button == 'Plant':
                    type = 1
                    sg.popup('{} organism_type is plant, please wait for a while.'.format(ProSeq.id))
                    window.close() 
                if button == 'Fungi':
                    type = 2
                    sg.popup('{} organism_type is fungi, please wait for a while.'.format(ProSeq.id))
                    window.close() 
            else:
                break
    
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        #需要Chrome浏览器(注：版本需对应，否则可能无法正常运行)
        s = Service(r"./chromedriver.exe")
        driver = webdriver.Chrome(service = s, options=options)
        driver.get(url)
        organism_type = driver.find_elements(By.NAME,"organism_type")[type]
        input_method = driver.find_elements(By.NAME,"input_type")[0]
        textarea = driver.find_element(By.NAME,"fasta_input")
        submit_checkbox = driver.find_element(By.NAME,"submit_sequence")
        
        organism_type.click()
        input_method.click()
        textarea.send_keys(ProSeq)
        submit_checkbox.click()

        sleep(10) #所需时间较久
        el = driver.find_element(By.XPATH,"/html/body").text
        sg.popup('You sequences Subcellular localization is :', el[21:])
        

#FDserver折叠速率预测
def fold_rate(filename):
    url="http://ibi.hzau.edu.cn/FDserver/cido.php"
    ProFoldingRate = {}
    for ProSeq in SeqIO.parse(filename, "fasta"):
        inputs = {'textarea': ProSeq, 'radiobutton': 'Unknown',
            'ButtonRatePred': 'Predict Folding Rate'}
        params = bytes(urlencode(inputs),encoding='utf-8')
        f = urlopen(url, params) #open url with post method
        results = f.read()
        f.close()
        result = str(results,'utf-8')[-15:-5]
        #将结果保存到字典中
        ProFoldingRate.update({ProSeq.id : result})
        sleep(2)
    sg.popup_scrolled('You sequences folding rate is :', ProFoldingRate,size=(150, 30))


#定义窗口样式
sg.SetOptions (background_color='#9FB8AD',
       text_element_background_color='#9FB8AD',
       element_background_color='#9FB8AD',
       scrollbar_color=None,
       input_elements_background_color='#F7F3EC',
       progress_meter_color = ('green', 'blue'),
       button_color=('white','#475841'),
       font =('Calibri',12,'bold'))    


#定义可选button和内容样式 
layout =[
        [sg.Text('SeqAnalyze Tools', font =('Calibri', 20, 'bold'))],
        [sg.Text('Enter protein sequences here:', font =('Calibri', 12, 'bold')),sg.ReadButton('File', size = (5,1))],
        [sg.Multiline(size = (20,3), key = '_Submit_',right_click_menu=right_click_menu),sg.ReadButton('Submit', size = (8,1))],
        [sg.Text('_'*32,font = ('Calibri', 12))],
        [sg.ReadButton('ID', size = (15,1)),sg.ReadButton('Length', size = (15,1))],
        [sg.ReadButton('Weight', size = (15,1)),sg.ReadButton('Hydrophobicity', size = (15,1))],
        [sg.ReadButton('Amino acid frequency',size = (32,2))],
        [sg.ReadButton('Subcellular localization', size = (32,2))],
        [sg.ReadButton('Folding rate prediction', size = (32,2))],
        ]

window = sg.Window('SeqAnalyze Tools').Layout(layout)

multline:sg.Multiline = window['_Submit_']


while True:
    button, value = window.Read()
    if button is not None:  
        if button == 'File':
            filename = open_file()
        if button in right_click_menu[1]:
            multline_operate(button, window, multline)
        if button == 'Submit':
            filename = input_file(value['_Submit_'][:-1])
        if button == '_Submit_':
            window['_Submit_'].update(value['_Submit_'][:-1],justification='l')
        if button == 'ID':
            seq_ID(filename)
        if button == 'Length':
            seq_len(filename)
        if button == 'Weight':
            seq_weight(filename)
        if button == 'Hydrophobicity':
            seq_hydrophobicity(filename)
        if button == 'Amino acid frequency':
            aa_freq(filename)
        if button == 'Subcellular localization':
            sub_local(filename)
        if button == 'Folding rate prediction':
            fold_rate(filename)
    else:
        break  



# %%
