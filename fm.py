#       fm.py
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

import math
import alsaaudio
import struct
from collections import deque

FRAME_RATE = 12000
NCHANNELS = 1
PERIOD=500
MAXINPUT=2**30
NSAMPLES=FRAME_RATE*10


class Sine:
	'''A sine wave oscillator.'''
	def __init__(self, amp=1.0, freq=440, phase=0.0,sr=FRAME_RATE):
		self.amp = amp
		self.freq = float(freq)
		self.phase = phase
		self.sr = sr
		self.diff=self.freq/self.sr
	def next(self,dev=0.0,amp=1,freqdev=0.0):
		'''phase is between 0 and 1'''
		if( self.phase > 1.0 ):
			self.phase=0.0
		self.diff=(self.freq+freqdev)/self.sr
		v = math.sin(self.phase * 2 * math.pi+dev)
		self.phase += self.diff
		
		return amp * v * self.amp
		
class Saw:
	'''A saw wave oscillator.'''
	def __init__(self, amp=1.0, freq=440, phase=0.0,sr=FRAME_RATE):
		self.amp = amp
		self.freq = float(freq)
		self.phase = phase
		self.sr = sr
		self.diff=self.freq/self.sr
	def next(self,dev=0.0,amp=1,freqdev=0):
		'''phase is between 0 and 1'''
		if( self.phase > 1.0 ):
			self.phase=0.0
		self.diff=(self.freq+freqdev)/self.sr
		v = self.phase
		self.phase += self.diff
		
		return amp * v * self.amp

class Lpf:
	"A simple rc lpf"
	def __init__(self, cutoff=440, sr=FRAME_RATE):
		self.last_out=0
		self.alpha=1/(1+sr/(2*math.pi*cutoff))
	def next(self,input=0):
		lp_out = (self.alpha*input + (1-self.alpha)*self.last_out)
		self.last_out=lp_out
		return lp_out
		
class Expenv:
	"exponential envelope"
	def __init__(self, tau=2.0,amp=1.0,sr=FRAME_RATE):
		self.time=0
		self.tau=tau
		self.amp=amp
		self.sr=sr
	def next(self,t=0):
		self.time+=1
		if(t!=0):
			self.time=0
		return self.amp*math.e**(-self.time/self.tau/self.sr)


#~ please write this thing for me
#~ class Adsr:
	#~ "ADSR envelope for amplitude shaping"
	#~ def __init__(self, attack=1.0/6.0, sr=FRAME_RATE ):
		#~ self.count=0
	#~ def next(self):
		#~ if (self.count < attack*sr):
			#~ return self.count/(sr*attack)
		#~ else:
			#~ if (self.count < decay):
				#~ return 1.0-(self.count-self.decay)*(0.25/
			#~ 

oscc=Sine(freq=250.0,amp=MAXINPUT)
oscm=Sine(freq=300.0,amp=1.0)
aenv=Expenv(amp=1.0,tau=1.0)
ienv=Expenv(amp=3.0,tau=1.0)

a=alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NORMAL, card='default')
a.setrate(FRAME_RATE)
a.setchannels(NCHANNELS)
a.setformat(alsaaudio.PCM_FORMAT_S32_LE)
a.setperiodsize(PERIOD)
per=PERIOD*NCHANNELS
list1=[]

for i in range(NSAMPLES):
	if(per>0):
		#t=osc1.next(freqdev=osc2.next(amp=1000,freqdev=osc3.next(amp=100)))
		t=aenv.next()*oscc.next(dev=(ienv.next()*oscm.next()))
		
		list1.append(t)
		per-=1
	else:
		per=PERIOD*NCHANNELS
		s=struct.pack('<'+NCHANNELS*PERIOD*'l',*list1)
		a.write(s)
		list1=[]
