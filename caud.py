#! /usr/bin/env python
from __future__ import division

import argparse, sys, os, os.path, glob
import sys,os.path,struct

from lxml import etree

def writeHD(ofl, frmt) :
  assert frmt in [3,6]
  
  ofl.write("dns.")
  ofl.write(b'\x20\x00\x00\x00')
  ofl.write(b'\xff\xff\xff\xff')
  ofl.write(b'\x06\x00\x00\x00' if frmt == 6 else b'\x03\x00\x00\x00')
  ofl.write(b'D\xac\x00\x00')
  ofl.write(b'\x01\x00\x00\x00')
  for i in range(2) :
    ofl.write(b'\x00\x00\x00\x00')
  
def packau(ofl, hdfn, aufiles) :
  #assert not os.path.exists(ofn)
  sizes = []
  fdone, remaining = [], []
  #with open(ofn, 'wb') as ofl, open(hdfn, 'wb') :
  if 1:
    lfrmt = None
    for fn in aufiles:
      assert os.path.exists(fn), fn
      with open(fn, 'rb') as f:
        hdsize = 6*4
        b = f.read(hdsize)
        assert len(b) == hdsize
        assert b[3::-1] == ".snd"
        offset = struct.unpack("<L", b[4:8])[0]
        sz = struct.unpack("<l", b[8:12])[0]    
        frmt = struct.unpack("<L", b[12:16])[0]
        assert frmt in [3,6], fn
        assert offset >= 32
        smprate = struct.unpack("<L", b[16:20])[0]
        chans = struct.unpack("<L", b[20:24])[0]
        assert smprate == 44100
        assert chans == 1

        if lfrmt is None :
          writeHD(ofl, frmt)
          lfrmt = frmt

        if frmt != lfrmt :
            remaining.append(fn)
          #assert frmt == lfrmt, (fn,  frmt , lfrmt, len(aufiles))
        else :
          fdone.append(fn)
          
          hdfn.write(b)

          #print fn,offset, sz, smprate, chans, 
          b1 = f.read(offset - hdsize)
          hdfn.write(b1)

          if sz > 0 :
            b1 = f.read(sz)
            assert len(b1) == sz
          else :
            b1 = f.read()
          ofl.write(b1)
          sizes.append((offset,len(b1)))
          #print len(b1)
  ofl.close()
  hdfn.close()
  #if remaining :
  #  print "***", remaining
  return lfrmt,sizes,fdone,remaining
  
parser = argparse.ArgumentParser(description = \
"""caud (Compress AUDacity) compresses an audacity project. Unlike the broken audacity
 option "File|Save a compressed ..." caud preserves the project in full. The decompressed
 version is identical to the source (with '-f wv') and almost identical with '-f ogg',
 where the audio samples may differ slightly because of the lossy nature of ogg-vorbis
 (i.e. due to the compression-decompression cycle). Obviously the ogg files are
 substantially smaller.
 cuad creates a single (tar) file. If your project was 'awesom.aup', caud will create
 'awesom.aup.save.tar.gz'. The original project is not modified in any way. It is HIGHLY
 RECOMMENDED that you verify the project decompresses correctly before deleting the
 original. Seriously!. You can choose the level of ogg compression but this is it. caud
 uses the installed 'sox' and 'tar' - make sure those two are installed on your system.""")  

parser.add_argument("-f", "--format", default = "wv",
                    help="'wv' (WavPack lossless audio compression) or 'ogg' (lossy vorbis).")
parser.add_argument("-q", "--quality", default = None, help="-1 to 10. ignored for wv.")
parser.add_argument("-p", "--progress", default = False, action="store_true", help="verbose progress messages.")

parser.add_argument("project", metavar="FILE", help = "Audacity project file (.aup)")
parser.add_argument("dir", metavar="DIR", help="work directory for all temporary files ('/tmp' or similar).")

options = parser.parse_args()

assert options.dir is not None
assert os.path.exists(options.project)
assert options.format in set(["wv","ogg"])

basedir = os.path.dirname(options.project).rstrip('/').strip()
options.dir = options.dir.rstrip('/')

if basedir == options.dir :
  print >> sys.stderr, "save directory must be different than project."
  sys.exit(1)

aud = etree.parse(options.project)
root = aud.getroot()

if root.nsmap :
  assert len(root.nsmap) == 1
  namespace = {'ns' : root.nsmap.values()[0]}
else :
  namespace = None
if basedir :
  base = basedir + '/'
else :
  base = ''
base = base + root.attrib['projname'] + '/'
# print basedir, base
aufiles = set(glob.glob(base + '*/*/*.au'))
# print "**",(base + '*/*/*.au'), len(aufiles)

aufiles = dict([(os.path.basename(f),f) for f in aufiles])

bundle = []
# for track in root.findall('ns:wavetrack', namespaces = namespace) :
#   for clip in track.findall('ns:waveclip', namespaces = namespace) :
#     for seq in clip.findall('ns:sequence', namespaces = namespace) :
#       bundle.append([])
#       for waveblock in seq.findall('ns:waveblock', namespaces = namespace):
#         for sb in waveblock.findall('ns:simpleblockfile', namespaces = namespace):
#           if 'filename' in sb.attrib:
#             assert sb.attrib['filename'] in aufiles, aufiles
#             #print track.attrib['name'],aufiles[sb.attrib['filename']]
#             bundle[-1].append(aufiles[sb.attrib['filename']])
#       if not bundle[-1] :
#         bundle.pop(-1)
#       else :
#         bundle[-1] = (track,bundle[-1])

for track in root.findall('ns:wavetrack', namespaces = namespace) :
  bundle.append([])
  for clip in track.findall('ns:waveclip', namespaces = namespace) :
    for seq in clip.findall('ns:sequence', namespaces = namespace) :
      for waveblock in seq.findall('ns:waveblock', namespaces = namespace):
        for sb in waveblock.findall('ns:simpleblockfile', namespaces = namespace):
          if 'filename' in sb.attrib:
            assert sb.attrib['filename'] in aufiles, (aufiles, sb.attrib['filename'])
            #print track.attrib['name'],aufiles[sb.attrib['filename']]
            bundle[-1].append(aufiles[sb.attrib['filename']])
  if not bundle[-1] :
    bundle.pop(-1)
  else :
    bundle[-1] = (track,bundle[-1])
        
import tempfile, shutil, subprocess

mfile = options.dir + '/' + os.path.basename(options.project) + '.master'
if not os.path.exists(os.path.dirname(mfile)) :
  os.makedirs(os.path.dirname(mfile))

if options.format == 'ogg' and options.quality is not None:
  soxopts = ['-C', options.quality]
else :
  soxopts = []
  
master = file(mfile, 'w')
fls = []

progress = options.progress
if progress: print >> sys.stderr, len(bundle), "bundles",

while bundle:
  track,files = bundle.pop(0)
  ##if any(['e00036ae.au' in f for f in files]) : print "has"
  
  audata = tempfile.NamedTemporaryFile(delete=False, prefix="ausv", suffix = ".au", dir = options.dir)
  hddata = tempfile.NamedTemporaryFile(delete=False, prefix="ausv", dir = options.dir)
  frmt,sizes,files,remaining = packau(audata, hddata, files)
  if remaining :
    bundle.insert(0,(track,remaining))
    
  oname = audata.name[:-3] + '.' + options.format
  if frmt == 6 :
    subprocess.check_call(["sox", "-e", "floating-point", "-b", "32", audata.name] + soxopts + [oname])
  else :
    assert frmt == 3
    subprocess.check_call(["sox", "-e", "signed-integer", "-b", "16", audata.name] + soxopts + [oname])
    
  os.remove(audata.name)
  if progress: print >> sys.stderr, ".",
  
  h,a = 0,0
  print >> master, os.path.basename(oname) + '\t' + os.path.basename(hddata.name) + '\t' + str(frmt) + '\t',
  for f,(hsize,asize) in zip(files, sizes) :
    if f.startswith(basedir + '/') :
      f = f[len(basedir) + 1:]
    print >> master, "'" + f.encode("utf-8") + "'", h, h+hsize, a, a+asize,
    h += hsize
    a += asize
  print >> master
  fls.extend([os.path.basename(oname),os.path.basename(hddata.name)])
fls.append(os.path.basename(master.name))
shutil.copy(options.project, options.dir + '/')
fls.append(os.path.basename(options.project))
master.close()

if progress: print >> sys.stderr, ", packing",

p = subprocess.Popen(["tar", "cfz", os.getcwd() + '/' + os.path.basename(options.project) + '.save.tar.gz']
                     + fls, cwd = options.dir)
s = p.wait()
assert s == 0

if progress: print >> sys.stderr, ", done"

for f in fls:
  os.remove(options.dir + '/' + f)
