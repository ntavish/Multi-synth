#       clarinet.py
#       
#       Copyright 2010 tavish <tavish.naruka@gmail.com>

#clarinet physical model


from Tkinter import *
from math import pi
import alsaaudio, audioop
from math import sin
import struct
from random import random
from multiprocessing import Process
from multiprocessing import Value
from time import sleep
from collections import deque
import wave

def setembrochure():
	"""
	this is called to synchronize the embrochure 
	variable upon clicking the set button in gui
	this is the simplest way i know
	"""
	em.value=app.sc.get()
def quit():
	"""
	quit
	"""
	root.destroy()
	clar.terminate()
	mic.terminate()
def microphone():
	"""
	continuosly(with breaks) takes input from microphone
	and outputs maximum amplitude to output volume
	could be changes to giving out average
	"""
	global mouth_pressure
	inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)

	# Set attributes: Mono, 8000 Hz, 16 bit little endian samples
	inp.setchannels(1)
	inp.setrate(8000)
	inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

	inp.setperiodsize(100)

	while True:
		# Read data from device
		l,data = inp.read()
		if l:
			# Return the maximum of the absolute value of all samples in a fragment.
			mouth_pressure.value=audioop.max(data, 2)<<16
		sleep(.001)

def reedtable(hdel1):
	"""
	reflection from the reed dependant on the embrochure
	"""
	hdel1/=MAXINPUT
	ccc=EMBROCHURE_OFFSET/MAXINPUT
	if hdel1<ccc:
		return 1-(ccc-hdel1)/(1+ccc)
	else:
		return 1	
	
def keypress(event):
	"""
	sets the value of note pressed, or quit on escape
	"""
	global var
	if event.keysym == 'Escape':
		root.destroy()
		clar.terminate()
		mic.terminate()
	x = event.char
	x=x.lower()
	if x == "z":
		var.value=440.0
	if x == "s":
		var.value=466.16
	if x == "x":
		var.value=493.88
	if x == "c":
		var.value=523.25
	if x == "f":
		var.value=554.36
	if x == "v":
		var.value=587.32
	if x == "g":
		var.value=622.25
	if x == "b":
		var.value=659.25
	if x == "n":
		var.value=698.45
	if x == "j":
		var.value=739.98
	if x == "m":
		var.value=783.99
	if x == "k":
		var.value=830.61
	if x == ",":
		var.value=880.0
	if x == "l":
		var.value=932.32
	if x == ".":
		var.value=997.76
	if x == "/":
		var.value=1046.50
	if x == "'":
		var.value=1108.73
	
	if x == "q":		#a
		var.value=220.0
	if x == "2":
		var.value=233.08
	if x == "w":
		var.value=246.9
	if x == "e":
		var.value=261.62
	if x == "4":
		var.value=277.18
	if x == "r":		#d
		var.value=293.66
	if x == "5":
		var.value=311.13
	if x == "t":
		var.value=329.62
	if x == "y":
		var.value=349.228
	if x == "7":
		var.value=369.94
	if x == "u":		#g
		var.value=391.99
	if x == "8":
		var.value=415.3

def clarinet():
	"""
	the main function using all the parameters to physically synthesize 
	the sound by exciting the system using the input
	"""
	global var
	global mouth_pressure
	global em
	a=alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NORMAL, card='default')
	a.setrate(FRAME_RATE)
	a.setchannels(NCHANNELS)
	a.setformat(alsaaudio.PCM_FORMAT_S32_LE)
	a.setperiodsize(PERIOD)
	
	
	f=wave.open("/home/tavish/clarinet.wav",'w')
	f.setparams((1,2,FRAME_RATE,10000,'NONE','noncompressed'))
	
	
	
	alpha=1/(1+FRAME_RATE/(2*pi*1500))
	
	alphaH=1/(1+(2*pi*1500)/FRAME_RATE)
	
	forwardDelay=deque([0 for i in range(MINFREQ_LEN)])
	backwardDelay=deque([0 for i in range(MINFREQ_LEN)])
			
	last_fdout=0
	last_lp_out=0
	last_out=0
	pm=0
	
	per=PERIOD*NCHANNELS
	outputbuffer=[]
	i=0
	emold=0.8
	fr=FRAME_RATE/2.5
	while 1:
		if i%10==0:
			N=int(round(FRAME_RATE/(var.value/OCTAVE)/2))
			pm=mouth_pressure.value
			emold=em.value
		#pm=MAXINPUT#*(1.5+0.5*sin(i/fr*pi*2)/2)
		i+=1
		if i>fr:
			i=0
		
		hdel=pm/2-backwardDelay[0]-emold*MAXINPUT
		pbf=pm/2-hdel*reedtable(hdel)
		
		forwardDelay.appendleft(pbf)
		
		#lpf	
		lp_out = (alpha*forwardDelay[-1] + (1-alpha)*last_lp_out)
		last_lp_out=lp_out
				
		backwardDelay.popleft()
		backwardDelay.append(0)
		backwardDelay[int(N-1)]=-lp_out
		
		#~ #hpf
		#~ out=alphaH*(last_out+forwardDelay[-1]-last_fdout)
		#~ last_out=out
		last_fdout=forwardDelay[-1]	
		
		forwardDelay.pop()		
		
		if(per>0):
			outputbuffer.append((last_fdout-lp_out))#*(1.5+0.5*sin(i/fr*pi*2)/2))
			per-=1
		else:
			per=PERIOD*NCHANNELS
			s=struct.pack('<'+NCHANNELS*PERIOD*'l',*outputbuffer)
			f.writeframes(s)
			a.write(s)
			outputbuffer=[]		
	a.close()
class App:
	"""the gui class"""
	def __init__(self, master):
		frame = Frame(master)
		frame.pack()
		self.button = Button(frame, text="QUIT", fg="red", command=quit)
		self.button.pack(side=LEFT)
		self.hi_there = Button(frame, text="set",command=setembrochure)
		self.hi_there.pack(side=LEFT)
		self.sc=Scale(frame,label="embrochure",orient=HORIZONTAL,from_=0.0,to=1.0,resolution=0.02,length=200)
		self.sc.set(0.2)
		self.sc.pack(side=RIGHT)
		self.sc2=Scale(frame,label="volume",orient=HORIZONTAL,from_=1,to=4,resolution=1,length=200)
		self.sc2.set(2)
		self.sc2.pack(side=RIGHT)
		def qq():
			frame.quit()
if __name__ == '__main__':
	FRAME_RATE = 32000
	NCHANNELS = 1
	PERIOD=500
	OCTAVE=1			#1=4th,2=3rd,0.5=5th
	MINFREQ_LEN=int(round(FRAME_RATE/(110.0/OCTAVE)/2))
	MAXINPUT=2**31
	EMBROCHURE_OFFSET=MAXINPUT*0.5
	
	#the synchronized values between processes
	var = Value('f',660.0)
	em= Value('f',0.2)
	mouth_pressure = Value('f',0.0)
	
	root = Tk()
	app = App(root)
	root.bind_all('<Key>', keypress)
	
	#the always running processes
	clar=Process(target=clarinet)
	clar.start()
	mic=Process(target=microphone)
	mic.start()
	
	#gui main loop
	root.mainloop()
