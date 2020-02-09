# author:Zhoubin
# 02-04-2020
import requests                         
import json     
import time               
import itchat                            #  微信API文档: https://itchat.readthedocs.io/zh/latest/
from time import sleep
import schedule
## 程序功能：定时抓取IOT机台运行数据，按自定义规则(本例 totalDownTime > 30)收集指定字段信息,发送至微信指定好友(本例传至"文件传输助手"，即:自己传给自己)
## 微信实时监控IOT机器运行情况

class IOT_info():

    ''' 始初化 '''
    def __init__(self):                                          
        itchat.auto_login(hotReload=True)                               # 弹出二维码，微信扫码登录
        self.url='http://59.40.183.220:8888/realTimeMonitor/update'     # Web入口
        self.header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}
    
    ''' 抓取IOT信息 '''
    def get_produce_information(self): 
        text = '机台 图号 数量 运行时间^停机时间 报警信息 \t\n'
        response = requests.get(self.url,headers=self.header)
        data =response.json()                
        IOT_informations = data.get('serverinformations')
        for x in IOT_informations: 
            if int(x.get('totalDownTime')[:2])*60 + int(x.get('totalDownTime')[3:5]) > 30:  # 定义数据搜集规则，全例:if 停机时间(分钟) > 30
                text = text + '{} {} {} {}^{} {} {}\t\n'.format(x.get('machineId'),x.get('productName').replace('N/A',''),x.get('producedParts'),x.get('totalRunTime')[:5],x.get('totalDownTime')[:5],x.get('alarmMsg'),x.get('idleMsg'))
        text = text + '_____________________\t\n' + time.ctime(time.time())                 # 消息末行添加当前日期时间                                
        return text

    ''' 发送至微信 '''
    def send_to_Wechat(self):
        info = self.get_produce_information()
        if len(info) > 80:
            itchat.send(info,toUserName='filehelper')  # 发送text至微信文件传输助手,也可以定义为任意微信好友       

if __name__=='__main__':
    IOT = IOT_info()
    schedule.every(10).minutes.do(IOT.send_to_Wechat)
    while True:
        schedule.run_pending()
        time.sleep(1)