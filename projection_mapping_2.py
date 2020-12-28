# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 11:40:25 2018

@author: MetaMorph
"""
import os
import wx
import numpy as np
from PIL import Image
import MMCorePy
import cv2
import threading
import time
import pandas as pd
import datetime
import serial

def init_mmc(binning,exposure_time):
    mmc = MMCorePy.CMMCore()
    mmc.loadDevice('Camera', 'HamamatsuHam', 'HamamatsuHam_DCAM')
    mmc.initializeAllDevices()
    mmc.setCameraDevice('Camera')
    mmc.setProperty('Camera','Binning',binning)
    mmc.setProperty('Camera','Exposure',exposure_time)
    return mmc

def pilImg2wxImg(pilImg):
    wxImg = wx.EmptyImage(pilImg.size[0], pilImg.size[1])
    wxImg.SetData(pilImg.convert('RGB').tobytes())
    return wxImg

def np_gImg2wx_gImg(npImg):
    npImg = npImg*255.0/65535.0
    npImg = npImg.astype(np.uint8)
    pilImg = Image.fromarray(npImg)
    wxImg = pilImg2wxImg(pilImg)
    return wxImg
    
def normalize_image(npImg):
    img = (npImg.astype(np.float32)-npImg.min())/(npImg.max()-npImg.min())
    return img*65535.0

def snap4wx(mmc):
    mmc.snapImage()
    image = mmc.getImage()
    image = normalize_image(image)
    wxImg = np_gImg2wx_gImg(image)
    bitmap = wxImg.ConvertToBitmap()
    return bitmap

def write_pos(f,pos):
    f.write(str(pos.x)+'\n')
    f.write(str(pos.y)+'\n')
    
def draw_circle(dc,pos,r=2):
    x = pos.x - r
    y = pos.y - r
    dc.DrawEllipse(x, y, 2.*r, 2.*r)
    
def set_color(dc,R,G,B,A):
    dc.SetBrush(wx.Brush(wx.Colour(R, G, B, A)))
    dc.SetPen(wx.Pen(wx.Colour(R, G, B), 1))

def load_RGB(fname):
    colors = pd.read_csv(fname)
    R = colors["R"]
    G = colors["G"]
    B = colors["B"]
    return [R,G,B]

def set_wx_colour(RGB,n):
    return wx.Colour(int(RGB[0][n]),int(RGB[1][n]), int(RGB[2][n]))

def matrix_of_ImgPos_to_ProjectionPos(ipos1,ipos2,ppos1,ppos2):
    G = np.array([[ipos1[0], ipos1[1]],
                  [ipos2[0], ipos2[1]]])
    X = np.array([ppos1[0], ppos2[0]])
    Y = np.array([ppos1[1], ppos2[1]])
    F1 = np.dot(np.linalg.inv(G),X)
    F2 = np.dot(np.linalg.inv(G),Y)
    F = np.array([[F1[0], F1[1]],
                  [F2[0], F2[1]]])
    #F = F.astype(np.int32)
    return F

def matrix_of_ImgPos_to_ProjectionPos3(ipos1,ipos2,ipos3,ppos1,ppos2,ppos3):
    G = np.array([[ipos1[0], ipos1[1], 1],
                  [ipos2[0], ipos2[1], 1],
                  [ipos3[0], ipos3[1], 1]])
    X = np.array([ppos1[0], ppos2[0], ppos3[0]])
    Y = np.array([ppos1[1], ppos2[1], ppos3[1]])
    F1 = np.dot(np.linalg.inv(G),X)
    F2 = np.dot(np.linalg.inv(G),Y)
    F = np.array([[F1[0], F1[1],F1[2]],
                  [F2[0], F2[1],F2[2]],
                  [0.0  , 0.0  ,1.0  ]])
    #F = F.astype(np.int32)
    return F

def load_xyxy(fname):
    r = np.zeros(4)
    i = 0
    with open(fname,'r') as f:
        for num in f:
            r[i] = np.int(num)
            i = i + 1
    xy1 = r[0:2]
    xy2 = r[2:4]
    #print fname+str(xy1)+srt(xy2)
    return xy1,xy2

def set_colors_of_bg_c(n,RGB_bg,RGB_c1):
    color_c1 = set_wx_colour(RGB_c1,n)
    color_bg = set_wx_colour(RGB_bg,n)
    return [color_bg, color_c1]

def set_ipos_ppos(F, pos):
    p = np.dot(F, pos.astype(np.float32))
    p = p.astype(np.int32)
    p = wx.Point(p[0],p[1])
    return p

class SendPositionEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)

    def SetPosition(self, pos):
        self.pos = pos

    def GetPosition(self):
        return self.pos
class SendRecEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
    def SetNum(self, n):
        self.num = n
    def GetNum(self):
        return self.num
    def SetFlag(self,f):
        self.flag = f
    def GetFlag(self):
        return self.flag
    
myEVT_TO_SEND = wx.NewEventType()
EVT_TO_SEND = wx.PyEventBinder(myEVT_TO_SEND, 1)
myEVT_TO_SEND_POS = wx.NewEventType()
EVT_TO_SEND_POS = wx.PyEventBinder(myEVT_TO_SEND_POS, 1)

class LivePanel(wx.Frame):
    def __init__(self, parent, title,binning,exposure_time):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY,title=title)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        self.mmc = init_mmc(binning,exposure_time)
        self.bitmap = snap4wx(self.mmc)
        
        self.SetSize((self.bitmap.Size.x+16,self.bitmap.Size.y+39))
        self.draw_flag = True
        
    def OnCloseWindow(self,event=None):
        self.draw_flag = False
        wx.Exit()

    def OnPaint(self, evt):
        if self.draw_flag == True:
            self.bitmap = snap4wx(self.mmc)
            
            pdc = wx.BufferedDC(wx.PaintDC(self))
            try:
                dc = wx.GCDC(pdc)
            except:
                dc = pdc
            dc.Clear()
            dc.DrawBitmap(self.bitmap, 0, 0, True)

            self.Refresh(False)

class CalibrationPanel(wx.Frame):
    def __init__(self, parent, title,binning,exposure_time,set_file):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY,title=title)

        menu_file = wx.Menu()
        menu_file.Append(1, 'Save')
        menu_bar = wx.MenuBar()
        menu_bar.Append(menu_file, 'File')
        self.SetMenuBar(menu_bar)
        self.set_file = set_file

        self.pos_l = wx.Point(0, 0)
        self.pos_r = wx.Point(0, 0)
        self.mouseLeftFlag = False
        self.mouseRightFlag = False

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseRightDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRightUp)
        self.Bind(wx.EVT_MENU,self.selectMenu)
        
        self.mmc = init_mmc(binning,exposure_time)
        self.bitmap = snap4wx(self.mmc)
        
        self.SetSize((self.bitmap.Size.x+16,self.bitmap.Size.y+59))
        
    def selectMenu(self,e):
        if e.GetId() == 1:
            with open(self.set_file,'w') as f:
                write_pos(f,self.pos_l)
                write_pos(f,self.pos_r)
    
    def OnMouseLeftDown(self, e):
        self.pos_l = e.GetPosition()
        self.mouseLeftFlag = True
        self.Refresh(False)
        self.ev = wx.EVT_PAINT
        evt = SendPositionEvent(myEVT_TO_SEND, self.GetId())
        evt.SetPosition(self.pos_l)
        self.GetEventHandler().ProcessEvent(evt)
        
    def OnMouseRightDown(self, e):
        self.pos_r = e.GetPosition()
        self.mouseRightFlag = True
        self.Refresh(False)
        self.ev = wx.EVT_PAINT
        evt = SendPositionEvent(myEVT_TO_SEND, self.GetId())
        evt.SetPosition(self.pos_r)
        self.GetEventHandler().ProcessEvent(evt)
        
    def OnMouseLeftUp(self,e=None):
        self.mouseLeftFlag = False
    
    def OnMouseRightUp(self,e=None):
        self.mouseRightFlag = False

    def OnPaint(self, evt):
        self.bitmap = snap4wx(self.mmc)
            
        pdc = wx.BufferedDC(wx.PaintDC(self))
        try:
            dc = wx.GCDC(pdc)
        except:
            dc = pdc
        dc.Clear()
        dc.DrawBitmap(self.bitmap, 0, 0, True)
        
        set_color(dc,255,0,0,64)
        draw_circle(dc,self.pos_l,r=2)
            
        set_color(dc,0,255,0,64)
        draw_circle(dc,self.pos_r,r=2)
        
        self.Refresh(False)

class DrawPanel(wx.Frame):
    def __init__(self,parent, title):
        wx.Frame.__init__(self,parent, title=title)
        pos,size = load_xyxy("ProjectionPanel_Pos_Size.txt")
        self.bpos,self.bsize = load_xyxy("Projector_Box_xy_size.txt")
        self.SetPosition((pos[0], pos[1]))
        self.SetSize((size[0],size[1]))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Refresh()
        
    def OnPaint(self,evt):
        dc = wx.ClientDC(self)
        dc.SetBackground(wx.Brush("Black"))
        dc.Clear()
        set_color(dc,0,255,255,64)
        x = self.bpos[0]
        y = self.bpos[1]
        bx = self.bsize[0]
        by = self.bsize[1]
        dc.DrawRectangle(x, y, bx, by)

class LiveDrawPanel(wx.Frame):
    def __init__(self,parent, title):
        wx.Frame.__init__(self,parent, title=title)
        pos,size = load_xyxy("ProjectionPanel_Pos_Size.txt")
        self.SetPosition((pos[0], pos[1]))
        self.SetSize((size[0],size[1]))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.RGB_bg = load_RGB('bg_color_set.csv')
        self.RGB_c1 = load_RGB('circle1_color_set.csv')

        n = 0
        self.color_bg, self.color_c1 = set_colors_of_bg_c(
                n, self.RGB_bg, self.RGB_c1)
        
        self.Refresh()
        
    def OnPaint(self,evt):
        dc = wx.ClientDC(self)
        dc.SetBackground(wx.Brush(self.color_bg))
        dc.Clear()

class SightPanel(wx.Frame):
    def __init__(self, parent, title,binning,exposure_time):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY,title=title)

        self.mouseLeftFlag = False
        self.pos = wx.Point(0, 0)
        self.draw_flag = True

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
      
        self.mmc = init_mmc(binning,exposure_time)
        self.bitmap = snap4wx(self.mmc)
        
        self.SetSize((self.bitmap.Size.x+16,self.bitmap.Size.y+39))
        
    def OnMouseLeftDown(self, e):
        self.pos = e.GetPosition()
        self.mouseLeftFlag = True
        self.Refresh(False)
        self.ev = wx.EVT_PAINT
        evt = SendPositionEvent(myEVT_TO_SEND, self.GetId())
        evt.SetPosition(self.pos)
        self.GetEventHandler().ProcessEvent(evt)
        
    def OnPaint(self, evt):
        if self.draw_flag == True:
            self.bitmap = snap4wx(self.mmc)
            
            pdc = wx.BufferedDC(wx.PaintDC(self))
            try:
                dc = wx.GCDC(pdc)
            except:
                dc = pdc
            dc.Clear()
            dc.DrawBitmap(self.bitmap, 0, 0, True)
        
            set_color(dc,255,0,0,64)
            draw_circle(dc,self.pos,r=2)
            
            self.Refresh(False)
        
    def OnMouseLeftUp(self,e=None):
        self.mouseLeftFlag = False

    def OnCloseWindow(self,event=None):
        self.draw_flag = False
        wx.Exit()

class ShootPanel(wx.Frame):
    def __init__(self,parent, title):
        wx.Frame.__init__(self,parent, title=title)
        pos,size = load_xyxy("ProjectionPanel_Pos_Size.txt")
        self.SetPosition((pos[0], pos[1]))
        self.SetSize((size[0],size[1]))
        
        ipos_bl,ipos_tr = load_xyxy("imgwindow_position.txt")
        ipos_tl = np.array([ipos_bl[0],ipos_tr[1]])
        self.bpos,bsize = load_xyxy("Projector_Box_xy_size.txt")
        bl = np.array([self.bpos[0],self.bpos[1]+bsize[1]])
        tr = np.array([self.bpos[0]+bsize[0],self.bpos[1]])
        tl = self.bpos
        self.F = matrix_of_ImgPos_to_ProjectionPos3(ipos_bl,ipos_tr,ipos_tl,bl,tr,tl)
        parent.Bind(EVT_TO_SEND, self.OnPaint)
        
        self.Refresh()

    def OnPaint(self,evt):
        dc = wx.ClientDC(self)
        dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0)))
        dc.Clear()
        ipos = evt.GetPosition()
        ipos = np.array([ipos.x,ipos.y,1])
        ppos = np.dot(self.F,ipos.astype(np.float32))
        ppos = ppos.astype(np.int32)
        ppos = wx.Point(ppos[0],ppos[1])
        set_color(dc,0,255,255,0)
        draw_circle(dc,ppos,r=2)

class RecPanel(wx.Frame):
    def __init__(self, parent, title,binning,exposure_time):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY,title=title)
        self.ser = serial.Serial(port="COM5", baudrate=9600)
        self.ser.write("*".encode())
        
        self.filenum = 1.0
        self.t_max = 30.0
        self.t_interval = 1.0/3.0
        
        self.mouseLeftFlag = False
        self.pos = wx.Point(0, 0)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)

        self.mmc = init_mmc(binning,exposure_time)
        self.bitmap = snap4wx(self.mmc)
        self.SetSize((self.bitmap.Size.x+16,self.bitmap.Size.y+39))
        
        self.draw_flag = True
        
        self.now = datetime.datetime.now()
        self.now = '{0:%Y%m%d%H%M}'.format(self.now)
        os.mkdir('images/'+self.now)
        self.t_start = time.time()
        t=threading.Thread(target=self.rec_timelapce)
        t.start()
        
    def rec_timelapce(self):
        while self.filenum <= self.t_max/self.t_interval:
            #timer = threading.Timer(1,self.rec)
            #timer.start()
            serData = self.ser.readline().strip().rsplit()
            value0 = float(serData[0])
            if(value0 == 1.0):
                evt = SendRecEvent(myEVT_TO_SEND, self.GetId())
                evt.SetNum(self.filenum)
                evt.SetFlag(True)
                self.GetEventHandler().ProcessEvent(evt)
                self.rec()
                evt = SendRecEvent(myEVT_TO_SEND, self.GetId())
                evt.SetNum(self.filenum)
                evt.SetFlag(False)
                self.GetEventHandler().ProcessEvent(evt)
                self.filenum = self.filenum+1
            #time.sleep(self.t_interval)
        
    def rec(self):
        self.mmc.snapImage()
        npImg = self.mmc.getImage()
        cv2.imwrite('images/'+self.now+'/img'+"{0:04d}".format(int(self.filenum))+'.tif',npImg)
        #np.savez('images/'+self.now+'/img'+"{0:04d}".format(self.filenum)+'.npz',npImg)
        npImg = normalize_image(npImg)
        wxImg = np_gImg2wx_gImg(npImg)
        self.bitmap = wxImg.ConvertToBitmap()
        self.Refresh(False)
        print self.filenum
        with open('images/'+self.now+'/img_time.txt','a') as f:
                f.write('img'+"{0:04d}".format(int(self.filenum))+','+str(time.time()-self.t_start)+'\n')
        
        
    def OnCloseWindow(self,event=None):
        self.draw_flag = False
        num = np.ceil(self.t_max/self.t_interval)
        self.filenum = num.astype(np.int32)
        wx.Exit()
    
    def OnPaint(self, evt):
        if self.draw_flag == True:
            pdc = wx.BufferedDC(wx.PaintDC(self))
            try:
                dc = wx.GCDC(pdc)
            except:
                dc = pdc
            dc.Clear()
            dc.DrawBitmap(self.bitmap, 0, 0, True)

            set_color(dc,255,0,0,64)
            draw_circle(dc,self.pos,r=2)

            self.Refresh(False)

    def OnMouseLeftDown(self, e):
        self.pos = e.GetPosition()
        self.mouseLeftFlag = True
        self.Refresh(False)
        self.ev = wx.EVT_PAINT
        evt = SendPositionEvent(myEVT_TO_SEND_POS, self.GetId())
        evt.SetPosition(self.pos)
        self.GetEventHandler().ProcessEvent(evt)

    def OnMouseLeftUp(self,e=None):
        self.mouseLeftFlag = False

    def OnCloseWindow(self,event=None):
        self.draw_flag = False
        wx.Exit()
            
class ProjectionPanel(wx.Frame):
    def __init__(self,parent, title):
        wx.Frame.__init__(self,parent, title=title)
        pos,size = load_xyxy("ProjectionPanel_Pos_Size.txt")
        self.SetPosition((pos[0], pos[1]))
        self.SetSize((size[0],size[1]))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        parent.Bind(EVT_TO_SEND, self.cycle_of_1rec)
        
        ipos_bl,ipos_tr = load_xyxy("imgwindow_position.txt")
        ipos_tl = np.array([ipos_bl[0],ipos_tr[1]])
        self.bpos,bsize = load_xyxy("Projector_Box_xy_size.txt")
        bl = np.array([self.bpos[0],self.bpos[1]+bsize[1]])
        tr = np.array([self.bpos[0]+bsize[0],self.bpos[1]])
        tl = self.bpos
        self.F = matrix_of_ImgPos_to_ProjectionPos3(ipos_bl,ipos_tr,ipos_tl,bl,tr,tl)
        parent.Bind(EVT_TO_SEND_POS, self.PosDef)

        self.RGB_c1 = load_RGB('circle1_color_set.csv')
        self.RGB_bg = load_RGB('bg_color_set.csv')
        self.RGB_ex = load_RGB('extra_bg_color_set.csv')
        self.p1 = wx.Point(0, 0)
        
        n = 0
        self.color_bg, self.color_c1 = set_colors_of_bg_c(
                n, self.RGB_bg, self.RGB_c1)
        
        self.Refresh(False)
        
    def cycle_of_1rec(self,evt):
        n = evt.GetNum()-1
        f = evt.GetFlag()
        if f==True:
            self.color_bg, self.color_c1 = set_colors_of_bg_c(
                n, self.RGB_bg, self.RGB_c1)
        elif f==False:
            self.color_bg, self.color_c1 = set_colors_of_bg_c(
                n, self.RGB_ex, self.RGB_c1)
        self.Refresh(False)
        self.Update()
    
    def OnPaint(self,evt):
        dc = wx.ClientDC(self)
        dc.SetBackground(wx.Brush(self.color_bg))
        dc.Clear()
        
        dc.SetBrush(wx.Brush(self.color_c1))
        dc.SetPen(wx.Pen(self.color_c1, 2))
        draw_circle(dc,self.p1,r=2)

    def PosDef(self,evt):
        ipos = evt.GetPosition()
        ipos = np.array([ipos.x,ipos.y,1])
        ppos = np.dot(self.F,ipos.astype(np.float32))
        ppos = ppos.astype(np.int32)
        ppos = wx.Point(ppos[0],ppos[1])
        self.p1 = ppos
        self.Refresh(False)