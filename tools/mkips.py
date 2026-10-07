import sys
a=open(sys.argv[1],'rb').read();b=open(sys.argv[2],'rb').read();assert len(a)==len(b)
runs=[];i=0
while i<len(a):
    if a[i]!=b[i]:
        j=i+1
        while j<len(a) and (a[j]!=b[j] or (j+1<len(a) and a[j+1]!=b[j+1])): j+=1
        while j-i>0xFFFF:
            runs.append((i,i+0xFFFF)); i+=0xFFFF
        runs.append((i,j)); i=j
    else: i+=1
out=bytearray(b'PATCH')
for s,e in runs:
    assert s!=0x454F46 and e<0xFFFFFF
    out+=s.to_bytes(3,'big')+(e-s).to_bytes(2,'big')+b[s:e]
out+=b'EOF'; open(sys.argv[3],'wb').write(out)
r=bytearray(a);p=bytes(out);k=5
while p[k:k+3]!=b'EOF':
    o=int.from_bytes(p[k:k+3],'big');n=int.from_bytes(p[k+3:k+5],'big');r[o:o+n]=p[k+5:k+5+n];k+=5+n
assert bytes(r)==b; print('ips ok',len(runs),'records')
