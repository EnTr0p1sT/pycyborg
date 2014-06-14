#!/usr/bin/env python2


###############################################################################
#                                                                             #
#       Copyright (c) 2014 EnTr0p1sT (entr0p1st@worldwidewyrd dot net,        #
#                          MD5 ID: 75cf1b154d75ea8a4dd4f91d82133f21)          #
#                                                                             #
###############################################################################

#Linux 'driver' for macro keys on Mad Catz CYBORG V7 keyboard

#This script takes bytes read from the hiddev usb file and finds the 'magic 
#one which determines which macro key is pressed.  This is then linked to a 
#command of the user's choice.  Make sure your user has permission for the /dev
#file.  It should be relatively easily modifiable for other similar keyboards.

#Usage: put it in your .xinitrc or something.  

#Config file format is an initial line with anything you like, followed by:
#
#Cx=/path/to/command
#
#for as many commands as you want to define, where 'x' is the number of the
#macro key, and without the hash at the beginning.

from binascii import hexlify
from subprocess import Popen, PIPE
from os.path import expanduser
import sys

#defining some constants
EVENT_LENGTH = 192 #magic number from playing with contents of hiddev0
DEVICE_ABBR = "Catz" #key word relating to keyboard to get from dmesg
BACK_STEPS = 7 #the number of characters preceeding the char of interest
SIGNATURE = '01' #the unique characters identifying a keypress
RC_FILE = expanduser('~') + '/.cyborgrc' #Default config file location


def read_macros(filename):
 macro=[]
 with open(filename) as macrofile:
  lines = macrofile.readlines()
 #strip newlines, and keep everything to the right of the '='
 for entry in lines:
  macro.append(entry[entry.find('=')+1:-1])
 return macro

def get_keyboard_addr(device):
 #Looks up the last dmesg entry mentioning the keyboard, and returns the
 #number of the hiddev corresponding to it in the /dev/usb tree
 
 #run dmesg and check for lines mentioning our device
 dmesg = Popen(["dmesg"], stdout=PIPE)
 grepDev = Popen(["grep", device], stdin=dmesg.stdout, stdout=PIPE)
 #filter these lines for those referring to hiddev
 grepCheck = Popen(["grep", "hiddev"], stdin=grepDev.stdout, stdout=PIPE)
 #if it has been plugged multiple times, get only the last line
 lastone = Popen(["tail", "-1"], stdin=grepCheck.stdout, stdout=PIPE)
 relline = lastone.communicate()[0]
 grepCheck.stdout.close()
 grepDev.stdout.close()
 dmesg.stdout.close()
 #now find where hiddev is in the string, and cut out the full addr
 index = relline.find("hiddev")
 return '/dev/usb/' + relline[index:index+7] 

def lookup_keypress(event):
 #gets the index of the signature, and backsteps to get the number
 index = event.find(SIGNATURE)
 hex = '0x' + event[index-BACK_STEPS]
 return MACRO[int(hex, 0)]

def parse_cmd(args):
 #If no args, read default file, else read given file, or fail
 file_err = "Unable to read default config in "
 usage_help = "Usage: python2 cyborg.py [optional: config file path]"
 if len(args) == 1:
  try:
   macro=read_macros(RC_FILE)
  except: 
   print file_err + RC_FILE
   sys.exit(1)
 elif len(args) == 2:
  try:
   macro=read_macros(args[1])
  except:
   print file_err + args[1]
   print usage_help
   sys.exit(1)
 else:
  print usage_help 
  sys.exit(1)
 return macro

#Read contents of file, then run infinite loop
MACRO = parse_cmd(sys.argv)
with open(get_keyboard_addr(DEVICE_ABBR)) as stream:
 while True: #shameless infinite loop!
  event=hexlify(stream.read(EVENT_LENGTH))
  Popen([lookup_keypress(event)])

