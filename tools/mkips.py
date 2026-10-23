import sys
a=open(sys.argv[1],'rb').read();b=open(sys.argv[2],'rb').read();assert len(b)>=len(a)
# a grown ROM (the FE8 ally attacks need 32 MB): the original is padded with 0xFF, the last byte is always written so the size is right,
# and offsets past 16 MB need IPS32 (4 byte offsets, header IPS32, trailer EEOF) because plain IPS offsets stop at 0xFFFFFF
orig_len=len(a); a=a+b'\xff'*(len(b)-len(a)); grown=len(b)>orig_len; big=len(b)>0xFFFFFF
runs=[];i=0
while i<len(a):
    if a[i:i+4096]==b[i:i+4096]: i+=4096; continue      # fast skip of identical blocks
    if a[i]!=b[i]:
        j=i+1
        while j<len(a) and (a[j]!=b[j] or (j+1<len(a) and a[j+1]!=b[j+1])): j+=1
        while j-i>0xFFFF:
            runs.append((i,i+0xFFFF)); i+=0xFFFF
        runs.append((i,j)); i=j
    else: i+=1
if grown and (not runs or runs[-1][1]<len(b)): runs.append((len(b)-1,len(b)))
out=bytearray(b'IPS32' if big else b'PATCH'); W=4 if big else 3; EOFM=b'EEOF' if big else b'EOF'
for s,e in runs:
    assert big or (s!=0x454F46 and e<0xFFFFFF)
    out+=s.to_bytes(W,'big')+(e-s).to_bytes(2,'big')+b[s:e]
out+=EOFM; open(sys.argv[3],'wb').write(out)
r=bytearray(a[:orig_len]);p=bytes(out);k=5
while p[k:k+len(EOFM)]!=EOFM:
    o=int.from_bytes(p[k:k+W],'big');n=int.from_bytes(p[k+W:k+W+2],'big')
    if o+n>len(r): r.extend(b'\xff'*(o+n-len(r)))
    r[o:o+n]=p[k+W+2:k+W+2+n];k+=W+2+n
assert bytes(r)==b; print('ips ok',len(runs),'records')
