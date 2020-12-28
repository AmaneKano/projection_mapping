# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 15:52:02 2018

@author: MetaMorph
"""

import projection_mapping_2 as pm
import wx

class MainWindow(wx.Frame): 
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent,id=wx.ID_ANY,title=title,size=((250,350)))
        panel0 = wx.Panel(self, wx.ID_ANY)
    
        panel1 = wx.Panel(panel0, wx.ID_ANY,size=((250,80)))
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.exposure_time = 100
        slider = wx.Slider(panel1, style=wx.SL_LABELS)
        slider.SetValue(self.exposure_time)
        slider.SetMin(10)
        slider.SetMax(1500)
        slider.Bind(wx.EVT_SLIDER, self.slider_value_change)
        box1 = wx.StaticBox(panel1, wx.ID_ANY, 'Exposure Time[ms]')
        sizer1 = wx.StaticBoxSizer(box1, wx.HORIZONTAL)
        sizer1.Add(slider,1)
        panel1.SetSizer(sizer1)
        
        panel2 = wx.Panel(panel0, wx.ID_ANY,size=((250,80)))
        self.binning = '4x4'
        r_1 = wx.RadioButton(panel2, 1, '1x1')
        r_2 = wx.RadioButton(panel2, 2, '2x2')
        r_3 = wx.RadioButton(panel2, 3, '4x4')
        box2 = wx.StaticBox(panel2, wx.ID_ANY, 'Binning')
        sizer2 = wx.StaticBoxSizer(box2, wx.HORIZONTAL)
        sizer2.Add(r_1,1)
        sizer2.Add(r_2,1)
        sizer2.Add(r_3,1)
        panel2.SetSizer(sizer2)
        panel2.Fit()
        self.Bind(wx.EVT_RADIOBUTTON, self.selected_radiobutton, r_1)
        self.Bind(wx.EVT_RADIOBUTTON, self.selected_radiobutton, r_2)
        self.Bind(wx.EVT_RADIOBUTTON, self.selected_radiobutton, r_3)
        
        panel3 = wx.Panel(panel0, wx.ID_ANY,size=((250,190)))
        b_cal = wx.Button(panel3, wx.ID_ANY, "calibraton")
        b_testcal = wx.Button(panel3, wx.ID_ANY, "test calibraton")
        b_live = wx.Button(panel3, wx.ID_ANY, "live")
        b_setpos = wx.Button(panel3, wx.ID_ANY, "set position")
        b_rec = wx.Button(panel3, wx.ID_ANY, "Rec")
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add(b_cal,1,wx.EXPAND)
        sizer3.Add(b_testcal,1,wx.EXPAND)
        sizer3.Add(b_live,1,wx.EXPAND)
        sizer3.Add(b_setpos,1,wx.EXPAND)
        sizer3.Add(b_rec,1,wx.EXPAND)
        panel3.SetSizer(sizer3)
        panel3.Fit()
        b_live.Bind(wx.EVT_BUTTON, self.live)
        b_rec.Bind(wx.EVT_BUTTON, self.rec)
        b_cal.Bind(wx.EVT_BUTTON, self.calibration)
        b_testcal.Bind(wx.EVT_BUTTON, self.test_calibration)
        b_setpos.Bind(wx.EVT_BUTTON, self.set_position)
        
        sizer0 = wx.BoxSizer(wx.VERTICAL)
        sizer0.Add(panel1,1)
        sizer0.Add(panel2,1)
        sizer0.Add(panel3,1)
        panel0.SetSizer(sizer0)
        panel0.Fit()
        
    def selected_radiobutton(self,event):
        num = event.GetId()
        if num==1 :
            self.binning = '1x1'
        elif num==2 :
            self.binning = '2x2'
        elif num==3:
            self.binning = '4x4'
    
    def slider_value_change(self,event):
        obj = event.GetEventObject()
        self.exposure_time = obj.GetValue()
        
    def live(self,e=None):
        frame1 = pm.LivePanel(self,"Live",self.binning,self.exposure_time)
        frame2 = pm.LiveDrawPanel(self,"DrawPanel")
        frame1.Show()
        frame2.Show()
        
    def rec(self,e=None):
        frame1 = pm.RecPanel(self,"Rec",self.binning,self.exposure_time)
        frame2 = pm.ProjectionPanel(frame1,"Projection")
        frame1.Show()
        frame2.Show()
        
    def calibration(self,e=None):
        frame1 = pm.CalibrationPanel(self,"Calibration",self.binning,
                                     self.exposure_time,"imgwindow_position.txt")
        frame2 = pm.DrawPanel(self,"DrawPanel")
        frame1.Show()
        frame2.Show()
        
    def test_calibration(self,e=None):
        frame1 = pm.SightPanel(self,"Test Calibration",self.binning,self.exposure_time)
        frame2 = pm.ShootPanel(frame1,"Projection")
        frame1.Show()
        frame2.Show()

    def set_position(self,e=None):
        frame1 = pm.CalibrationPanel(self,"Set Position",self.binning,
                                    self.exposure_time,"sight_position.txt")
        frame2 = pm.ShootPanel(frame1,"DrawPanel")
        frame1.Show()
        frame2.Show()
    
app = wx.App(False)
frame = MainWindow(None,"Main")
frame.Show()
app.MainLoop()
