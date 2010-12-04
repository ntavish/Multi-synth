#       alsa-string-optimized.py
#       
#       Copyright 2010 tavish <tavish.naruka@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


#plucked string model
#modify low pass filter
#modify damping


from Tkinter import *
import alsaaudio
from math import sin
import struct, random
from multiprocessing import Process
from time import sleep
from collections import deque
from math import pi

def keypress(event):
	if event.keysym == 'Escape':
		root.destroy()
		while len(p)>0:
			if len(p)>=1 :
				p[0].terminate()
				p.popleft()
	x = event.char
	
	if x == "z":
		var=440.0
	if x == "s":
		var=466.16
	if x == "x":
		var=493.88
	if x == "c":
		var=523.25
	if x == "f":
		var=554.36
	if x == "v":
		var=587.32
	if x == "g":
		var=622.25
	if x == "b":
		var=659.25
	if x == "n":
		var=698.45
	if x == "j":
		var=739.98
	if x == "m":
		var=783.99
	if x == "k":
		var=830.61
	if x == ",":
		var=880.0
	if x == "l":
		var=932.32
	if x == ".":
		var=997.76
	if x == "/":
		var=1046.50
	if x == "'":
		var=1108.73
	
	if x == "q":		#a
		var=220.0
	if x == "2":
		var=233.08
	if x == "w":
		var=246.9
	if x == "e":
		var=261.62
	if x == "4":
		var=277.18
	if x == "r":		#d
		var=293.66
	if x == "5":
		var=311.13
	if x == "t":
		var=329.62
	if x == "y":
		var=349.228
	if x == "7":
		var=369.94
	if x == "u":		#g
		var=391.99
	if x == "8":
		var=415.3
	
	
	try:
		var/=OCTAVE
		if len(p)>=MAXSTRINGS :
			p[0].terminate()
			p.popleft()
		temp = Process(target=sinusoidaloid,args=(var,))
		temp.start()
		p.append(temp)
	except:
		pass
def sinusoidaloid(var):
	var=int(round(var))
	N=FRAME_RATE/var
	a=alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NORMAL, card='default')
	a.setrate(FRAME_RATE)
	a.setchannels(NCHANNELS)
	a.setformat(alsaaudio.PCM_FORMAT_S32_LE)
	a.setperiodsize(PERIOD)

	#buffer = [ ((random()-0.5)*MAX) for i in range(N)]
	buffer = [0]*N

	buf=deque(buffer)
	list1=[]
	per=PERIOD*NCHANNELS
	
	last_lp_out=0
	
	##freq dep cutofff
	CUTOFF=5000+(var-440/OCTAVE)*20
	
	alpha=1/(1+FRAME_RATE/(2*pi*CUTOFF))
	g=0.996
	
	for i in range(NSAMPLES):
		if(i<N):
			#buf[i]=(int(random.getrandbits(31)))
			#buf[i]=(random.random()-0.5)*MAX
			#buf[i]=random.gauss(0,0.5)*MAX/4
			buf[i]=random.randint(-MAX,MAX)
			#buf[i]=random.choice([-MAX,MAX])			
		if(per>0):
			list1.append(buf[0])
			per-=1
		else:
			per=PERIOD*NCHANNELS
			s=struct.pack('<'+NCHANNELS*PERIOD*'l',*list1)
			a.write(s)
			list1=[]
		#lpf	
		lp_out = (alpha*buf[0] + (1-alpha)*last_lp_out)*g
		last_lp_out=lp_out
		
		buf.append(lp_out)
		buf.popleft()
	a.close()

def send():
	var=app.sc.get()
	global pp
	try:
		pp.terminate()
	except:
		pass
	pp = Process(target=sinusoidaloid,args=(var,))
	pp.start()
	
	
class App:
	"""the gui"""
	def __init__(self, master):
		frame = Frame(master)
		frame.pack()
		self.button = Button(frame, text="QUIT", fg="red", command=quit)
		self.button.pack(side=LEFT)
		self.hi_there = Button(frame, text="Play",command=send)
		self.hi_there.pack(side=LEFT)
		self.sc=Scale(frame,label="frequency",orient=HORIZONTAL,from_=1,to=1000,resolution=1,length=1000)
		self.sc.set(440)
		self.sc.pack(side=RIGHT)
		def qq():
			frame.quit()

if __name__=='__main__':

	FRAME_RATE = 32000
	NCHANNELS = 1
	PERIOD=400			#size of chunk of data to write to audio device, makes a huge diff in case of alsa
	NSAMPLES = 48000*5
	MAX=2**30-1
	MAXSTRINGS=4
	OCTAVE=2			#1=4th,2=3rd,0.5=5th
	CUTOFF=3500
	global p
	p=deque([])

	root = Tk()
	app = App(root)

	root.bind_all('<Key>', keypress)

	root.mainloop()
