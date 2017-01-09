# audacity-archive

'caud' (Compress AUDacity) compresses an audacity project. Unlike the broken audacity
option "File|Save a compressed ..." caud preserves the project in full. 'daud'
decompresses an archive. 

The decompressed version is identical to the source (with '-f wv') and almost identical
with '-f ogg', where the audio samples may differ slightly because of the lossy nature of
ogg-vorbis (i.e. due to the compression-decompression cycle). Obviously the ogg files are
substantially smaller.  cuad creates a single (tar) file. If your project was
'awesom.aup', caud will create 'awesom.aup.save.tar.gz'.

The original project is not modified in any way.

It is HIGHLY RECOMMENDED that you verify the project decompresses correctly before
deleting the original. Seriously!. You can choose the level of ogg compression but this is
it.

caud uses the installed 'sox' and 'tar' - make sure those two are installed on your
system.

