#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Zhoubin
# Created:Feb/11/2020 Modified:2020-02-14
# V2.0 由等分间隔时间触发微信发送IOT事件，修改为每天7:58、11:58、12:58、17:58,19:58定时发送
import wx                   # 界面
import wx.adv               # 界面advance
import requests             # 网络请求                    
import json                 # json数据结构解析
import itchat               # 微信API文档: https://itchat.readthedocs.io/zh/latest/
import time                 # 日期、时间
from apscheduler.schedulers.background import BackgroundScheduler    # 后台定时任务，非阻塞式
#from apscheduler.triggers.interval import IntervalTrigger           # 指定间隔时间循环执行程序,本例暂不用
from apscheduler.triggers.cron import CronTrigger                    # 指定时间循环执行程序

# 定义系统托盘
class MyTaskBarIcon(wx.adv.TaskBarIcon):
    ICON = "IOT.ico"          # 图标文件
    ID_RUN = wx.NewId()       # 菜单选项“运行程序”的ID
    ID_ABOUT = wx.NewId()     # 菜单选项“关于”的ID
    ID_EXIT = wx.NewId()      # 菜单选项“退出”的ID
    TITLE = "IOT assistant"   # 鼠标移动到图标上显示的文字

    # 初始化
    def __init__(self):
        wx.adv.TaskBarIcon.__init__(self)
        self.SetIcon(wx.Icon(self.ICON), self.TITLE)                 # 设置图标和标题
        self.Bind(wx.EVT_MENU, self.onRun_program, id=self.ID_RUN)   # 绑定“运行程序”选项的点击事件
        self.Bind(wx.EVT_MENU, self.onAbout, id=self.ID_ABOUT)       # 绑定“关于”选项的点击事件
        self.Bind(wx.EVT_MENU, self.onExit, id=self.ID_EXIT)         # 绑定“退出”选项的点击事件
    
    # "运行程序"选项的事件处理器
    def onRun_program(self,event):
        SendToWechatIOT_info().get_produce_information()
        SendToWechatIOT_info().delay_exec()
    
    # “关于”选项的事件处理器
    def onAbout(self, event):
        wx.MessageBox('程序功能：抓取IOT实时运行数据，传送至微信\n作者：Zhoubin\n最后更新日期：2020-2-11', "关于")

    # “退出”选项的事件处理器
    def onExit(self, event):
        wx.Exit()

    # 创建菜单选项
    def CreatePopupMenu(self):
        menu = wx.Menu()
        for mentAttr in self.getMenuAttrs():
            menu.Append(mentAttr[1], mentAttr[0])
        return menu

    # 获取菜单的属性元组
    def getMenuAttrs(self):
        return [('运行程序',self.ID_RUN),('关于', self.ID_ABOUT),('退出', self.ID_EXIT)]
                
class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self)
        MyTaskBarIcon()       #显示系统托盘图标

class MyApp(wx.App):
    def OnInit(self):
        MyFrame()
        return True

# IOT运行信息发送至指定微信好友
class SendToWechatIOT_info():
    def __init__(self):
        itchat.auto_login(hotReload=True)     # 弹出二维码，微信扫码登录                        
    
    # 实时抓取IOT机器运行信息
    def get_produce_information(self):
        url = 'http://192.168.9.164:88/realTimeMonitor/update'   # IOT 本地网络入口
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}        
        first_row = 'IOT assistant\n_____________________________\n机台|图号|数量|运行|停机|报警\n'
        text = ''         
        response = requests.get(url,headers=header)                                         
        data =response.json()
        IOT_informations = data.get('serverinformations')

        # 定义数据抓取规则
        for x in IOT_informations: 
            if x.get('states')==3:    # 红色警报
                text = text + '{} {}#{}#{}^{} {} {}\n'.format(x.get('machineId'),x.get('productName').replace('N/A',''),x.get('producedParts'),\
                x.get('totalRunTime')[:5],x.get('totalDownTime')[:5],x.get('alarmMsg'),x.get('idleMsg')) # 时间去除秒数[:5],图号N/A替换成空
            elif x.get('states')==1:  # 绿色,正常生产
                text = text + '{} {}#{}#{}^{}\n'.format(x.get('machineId'),x.get('productName').replace('N/A',''),\
                    x.get('producedParts'),x.get('totalRunTime')[:5],x.get('totalDownTime')[:5])
            elif x.get('states')==2:  # 黄色警报
                pass                  # 待补充
            elif x.get('states')==4:  # 灰色警报,OffLine
                text = text + '{} {}#{}#{}^{} {}\n'.format(x.get('machineId'),x.get('productName').replace('N/A',''),x.get('producedParts'),\
                x.get('totalRunTime')[:5],x.get('totalDownTime')[:5],'OffLine')
        if len(text) > 0:     # 信息非空白，则发送至微信
            msg = first_row + text + '_____________________________\n' + time.ctime(time.time()) # 末行添加当前日期时间
            #user = itchat.search_friends(name='张总')[0]['UserName']  # name=备注名
            #itchat.send(msg,toUserName=user)         # filehelper:文件传输助手
            itchat.send(msg,toUserName='filehelper')
            itchat.show_mobile_login()
        else:
            pass

    # 间隔指定时间抓取IOT信息、发送信息
    def delay_exec(self):
        sched = BackgroundScheduler()
        #tig = IntervalTrigger(minutes=30)       # 每隔30分钟执行一次get_produce_information
        # 每天定时在7:58、11:58、12:58、19:58微信发送一次数据
        tig = CronTrigger(day='1-31',hour='7,11,12,19',minute='58',end_date='2020-12-31')     
        sched.add_job(self.get_produce_information,tig)    
        sched.start() 

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop() 