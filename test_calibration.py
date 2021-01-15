# -*- coding: utf-8 -*-
"""
Created on Tue Feb 06 23:01:22 2018

@author: MetaMorph
"""

import wx
import numpy as np
from PIL import Image
import MMCorePy

def init_mmc():
    mmc = MMCorePy.CMMCore()
    mmc.loadDevice('Camera', 'HamamatsuHam', 'HamamatsuHam_DCAM')
    mmc.initializeAllDevices()
    mmc.setCameraDevice('Camera')
    return mmc

def pilImg2wxImg(pilImg):
    wxImg = wx.EmptyImage(pilImg.size[0], pilImg.size[1])
    wxImg.SetData(pilImg.convert('RGB').tobytes())
    return wxImg

def np_gImg2wx_gImg(npImg):
    width = len(npImg[:,0])
    height = len(npImg[0,:])
    npImg = npImg*255.0/65535.0
    npImg = npImg.astype(np.uint8)
    pilImg = Image.fromarray(npImg)
    wxImg = pilImg2wxImg(pilImg)
    return wxImg

class SendPositionEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)

    def SetPosition(self, pos):
        self.pos = pos

    def GetPosition(self):
        return self.pos

myEVT_TO_SEND = wx.NewEventType()
EVT_TO_SEND = wx.PyEventBinder(myEVT_TO_SEND, 1)

class SightPanel(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY,title=title)

        self.mouseLeftFlag = False
        self.pos = wx.Point(0, 0)
        self.draw_flag = True

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        self.mmc = init_mmc()
        self.mmc.setProperty('Camera','Binning','2x2')
        self.mmc.setProperty('Camera','Exposure',100)
        
        self.mmc.snapImage()
        image = self.mmc.getImage()
        width = len(image[:,0])
        height = len(image[0,:])
        self.SetSize(width,height)
        
        wxImg = np_gImg2wx_gImg(image)
        self.bitmap = wxImg.ConvertToBitmap()
        
    def OnMouseLeftDown(self, e):
        mpos = e.GetPosition()
        self.pos = mpos
        self.mouseLeftFlag = True
        self.Refresh(False)
        self.ev = wx.EVT_PAINT
        evt = SendPositionEvent(myEVT_TO_SEND, self.GetId())
        evt.SetPosition(self.pos)
        self.GetEventHandler().ProcessEvent(evt)
        
    def OnPaint(self, evt):
        if self.draw_flag == True:
            self.mmc.snapImage()
            image = self.mmc.getImage()
            wxImg = np_gImg2wx_gImg(image)
            self.bitmap = wxImg.ConvertToBitmap()
            
            pdc = wx.BufferedDC(wx.PaintDC(self))
            try:
                dc = wx.GCDC(pdc)
            except:
                dc = pdc
            dc.Clear()
            dc.DrawBitmap(self.bitmap, 0, 0, True)
        
            dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0, 64)))
            dc.SetPen(wx.Pen("RED", 2))
            r = 2
            x = self.pos.x - r
            y = self.pos.y - r
            dc.DrawEllipse(x, y, 2.*r, 2.*r)
            
            self.Refresh(False)
        
    def OnMouseLeftUp(self,e=None):
        self.mouseLeftFlag = False

    def OnCloseWindow(self,event=None):
        self.draw_flag = False
        wx.Exit()

class DrawPanel(wx.Frame):
    def __init__(self,parent, title):
        wx.Frame.__init__(self,parent, title=title)
        self.Refresh()
        parent.Bind(EVT_TO_SEND, self.OnPaint)
        

    def OnPaint(self,evt):
        dc = wx.ClientDC(self)
        dc.SetBackground(wx.Brush("Black"))
        dc.Clear()
        dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0, 64)))
        dc.SetPen(wx.Pen("RED", 2))
        r = 10
        pos = evt.GetPosition()
        x = pos.x - r
        y = pos.y - r
        dc.DrawEllipse(x, y, 2.*r, 2.*r)

app = wx.App(False)
frame1 = SightPanel(None,title="sight")
frame1.Show()
frame = DrawPanel(frame1,title="project")
frame.Show()
app.MainLoop()