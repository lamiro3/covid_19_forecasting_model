import time
import sys
import numpy as np 
import matplotlib.pylab as plt
from scipy.integrate import odeint
from selenium import webdriver
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

######################################## WebDriver #######################################
options = webdriver.ChromeOptions()
options.add_argument('headless') #크롬 브라우저 백그라운드로 실행
options.add_argument('disable-gpu') #gpu가속 disable

SIRdriver_KOR = webdriver.Chrome(r'COVID_19_forecasting_model\chromedriver.exe', chrome_options = options)
POPdriver_KOR = webdriver.Chrome(r'COVID_19_forecasting_model\chromedriver.exe', chrome_options = options)

SIRdriver_KOR.get('http://ncov.mohw.go.kr/')
POPdriver_KOR.get('https://superkts.com/population/all')

assert "코로나바이러스감염증-19(COVID-19)" in SIRdriver_KOR.title #title이 다음과 다르다면 오류 뜨게끔 함

SIRhtml_KOR = SIRdriver_KOR.page_source
POPhtml_KOR = POPdriver_KOR.page_source

SIRsoup_KOR = BeautifulSoup(SIRhtml_KOR, 'html.parser')
POPsoup_KOR = BeautifulSoup(POPhtml_KOR, 'html.parser')

######################################## GRAPH #######################################
class Graph():
    def SIR(self, x, t, beta, gamma): # t = 시간(일), beta = 감염의 효과율, gamma = 회복률 = 잠복기간의 역수
        s = x[0] # 전체 취약자수
        i = x[1] # 전체 감염자수
        r = x[2] # 전체 회복자수

        dsdt = -beta*s*i #시간에 따른 취약자수 변화율
        didt = beta*s*i - gamma*i #시간에 따른 감염자수 변화율
        drdt = gamma*i #시간에 따른 회복자수 변화율

        y = [dsdt, didt, drdt]
        return y
    
    def _plot(self, func, x, t, beta, gamma, N):
        result = odeint(func, x, t, args=(beta, gamma))
        plt.plot(t, result[:,0]/N*100, 'b', label='Susceptible') #취약자 동향 - 백분율
        plt.plot(t, result[:,1]/N*100, 'r', label='Infected') #감염자 동향 - 백분율
        plt.plot(t, result[:,2]/N*100, 'g', label='Recovered') #회복자 동향 - 백분율
        plt.xlabel('days')
        plt.ylabel('percentage of each population (%)')
        plt.title('Republic of Korea')
        plt.legend(loc="upper right")

######################################## Get Data #######################################
class get_KOR_Data():

    confirmed_data_IR = []
    confirmed_data_POP = []

    def __init__(self, confirmed_data_IR, confirmed_data_POP):
        self.confirmed_data_IR = confirmed_data_IR
        self.confirmed_data_POP = confirmed_data_POP

    def getIR(self, soup):
        for pre_data_1 in soup.find_all('ul', class_='liveNum'):
            confirmed_data_IR = pre_data_1.find_all('span', class_='num')
            for i in range(0, len(confirmed_data_IR)):
                confirmed_data_IR[i] = confirmed_data_IR[i].get_text()
        a = confirmed_data_IR[0]
        confirmed_data_IR[0] = a[4:]
        return confirmed_data_IR
    
    def getPOP(self, soup):
        for pre_data_2 in soup.find_all('article', class_='intro'):
            confirmed_data_POP = pre_data_2.find_all('b')
        confirmed_data_POP[0] = confirmed_data_POP[0].get_text()
        #a = confirmed_data_POP[0]
        #confirmed_data_POP[0] = a[:10]
        return confirmed_data_POP
    
    def convertToInt(self, _list):
        for i in range(0, len(_list)):
            _list[i] = _list[i].replace(',','') #천단위 쉼표 제거
            _list[i] = int(_list[i]) #자료형 변환
        return _list

class get_CHN_Data():
    confirmed_data_IR = []
    confirmed_data_POP = []

    def __init__(self, confirmed_data_IR, confirmed_data_POP):
        self.confirmed_data_IR = confirmed_data_IR
        self.confirmed_data_POP = confirmed_data_POP

class get_USA_Data():
    confirmed_data_IR = []
    confirmed_data_POP = []

    def __init__(self, confirmed_data_IR, confirmed_data_POP):
        self.confirmed_data_IR = confirmed_data_IR
        self.confirmed_data_POP = confirmed_data_POP

class get_WORLD_Data():
    confirmed_data_IR = []
    confirmed_data_POP = []

    def __init__(self, confirmed_data_IR, confirmed_data_POP):
        self.confirmed_data_IR = confirmed_data_IR
        self.confirmed_data_POP = confirmed_data_POP

######################################## Print #######################################
class MyWindow(QWidget, Graph):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.fig = plt.figure(figsize=(70,70)) #출력되는 그래프 크기
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)

        self.canvas.draw()

        self.setLayout(layout)

        self.setGeometry(300, 300, 700, 500)
        self.setWindowTitle("COVID-19 SIR forecasting model")

        self.show()

printGraph = Graph()
GKD = get_KOR_Data(list(), list())

pre_POP_KOR = GKD.convertToInt(GKD.getPOP(POPsoup_KOR)) #인구
pre_IR_KOR = GKD.convertToInt(GKD.getIR(SIRsoup_KOR)) #(순서대로) - [0]누적 확진자수, [1]회복자수(완치자수), [2]격리자수(치료자수), [3]사망자수

# <quit all drivers>
SIRdriver_KOR.quit()
POPdriver_KOR.quit()

# <constant>
covid_19_R0 = 2.25 #코로나 바이러스 기초감염재생산수
gamma_input = 1/14 #코로나 바이러스 잠복기간 = 약 14일 이내 --> 회복률은 잠복기간의 역수인 1/14

# <variable - korea>
Population_input_KOR = pre_POP_KOR[0] #모집단 인구
Susceptible = Population_input_KOR - pre_IR_KOR[1] - pre_IR_KOR[2]
Infected = pre_IR_KOR[2]
Recovered = pre_IR_KOR[1]
beta_input_KOR = gamma_input*covid_19_R0/Susceptible # beta = gamma*R0/S
t_input_KOR = np.linspace(0, 500) #시간 범위 설정(가로축 범위 설정) - 단위: 일(day)
x_input_KOR = [Susceptible, Infected, Recovered]

app=QApplication(sys.argv)
w=MyWindow()
printGraph._plot(printGraph.SIR, x_input_KOR, t_input_KOR, beta_input_KOR, gamma_input, Population_input_KOR)
sys.exit(app.exec_()) # exec_()가 루프를 생성하는 함수