#! /usr/bin/env python

from __future__ import division

import argparse, sys, os, os.path, glob, struct

def getAUdata(fn) :
  f = open(fn, 'rb')
  hdsize = 6*4
  b = f.read(hdsize)
  assert len(b) == hdsize
  assert b[3::-1] == ".snd" or b[3:0:-1] == ".sd", b[3:0:-1]
  offset = struct.unpack("<L", b[4:8])[0]
  sz = struct.unpack("<l", b[8:12])[0]    
  frmt = struct.unpack("<L", b[12:16])[0]
  assert frmt in [3,6]
  assert offset >= 32
  smprate = struct.unpack("<L", b[16:20])[0]
  chans = struct.unpack("<L", b[20:24])[0]
  assert smprate == 44100
  assert chans == 1
  #print fn,offset, sz, smprate, chans, 
  f.read(offset - hdsize)
  return f
  
parser = argparse.ArgumentParser(description =
  """daud decompresses an audacity archive created by 'caud'. That is all you need to know.""")

parser.add_argument("cproject", metavar="FILE")

options = parser.parse_args()

if not os.path.exists(options.cproject) :
  print >> sys.stderr, "Can't open file (",options.cproject,")"
  sys.exit(1)

if not options.cproject.endswith('.aup.save.tar.gz') :
  print >> sys.stderr, "Wrong extension (should be .aup.save.tar.gz)"
  sys.exit(1)
  
projectName = os.path.basename(options.cproject[:-len('.aup.save.tar.gz')])

if (os.path.exists(projectName + ".aup") or os.path.exists(projectName + "_data.aup")) :
  print >> sys.stderr, "(Cowardly) refusing to overwrite files."
  sys.exit(1)

import tempfile, shutil, subprocess

subprocess.check_call(["tar", "xf", options.cproject])

# print >> sys.stderr, "done extracting"

for l in file(projectName + '.aup.master') :
  l = l.strip();
  if not l : continue
  l = l.split('\t');   assert len(l) == 4
  caufile,hdfile,frmt = [x.strip() for x in l[:3]]
  assert os.path.exists(caufile) and os.path.exists(hdfile) and \
    any([caufile.endswith('.' + x) for x in ('wv','ogg')]) and int(frmt) in [3,6]
  aufile = os.path.splitext(caufile)[0] + '.au'
  # aufile = caufile[:-3] + '.au'
  if int(frmt) == 6 :
    subprocess.check_call(["sox", caufile, "-e", "floating-point", "-b", "32", "-L", aufile])
  else :
    subprocess.check_call(["sox", caufile, "-e", "signed-integer", "-b", "16", "-L", aufile])
  #import pdb
  #pdb.set_trace()
  files2dc = l[-1].split(' ')
  k = 0
  while k < len(files2dc) :
    assert files2dc[k][0] == "'"
    if files2dc[k][-1] != "'" :
      while files2dc[k][-1] != "'" :
        x = files2dc.pop(k+1)
        files2dc[k] = files2dc[k] + ' ' + x
    k += 5

  assert len(files2dc) % 5 == 0
  with getAUdata(aufile) as au, open(hdfile, 'rb') as hd:
    for k in range(0, len(files2dc), 5) :
      fl,hstart,hend,astart,aend = [files2dc[k]] + [int(x) for x in files2dc[k+1:k+5]]
      fl = fl.strip("'").decode('utf-8')
      #print fl
      if not os.path.exists(os.path.dirname(fl)) :
        os.makedirs(os.path.dirname(fl))
      with open(fl, 'wb') as afile:
        b1 = hd.read(hend - hstart); assert len(b1) == (hend - hstart), (fl, len(b1), (hend - hstart))
        afile.write(b1)
        b1 = au.read(aend - astart);  assert len(b1) == (aend - astart),(fl, len(b1) , (aend - astart))
        afile.write(b1)
        #afile.close()
  os.remove(aufile)
  os.remove(hdfile)
  os.remove(caufile)
os.remove(projectName + '.aup.master')
