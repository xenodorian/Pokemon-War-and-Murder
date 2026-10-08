# ----------------------------------------------------------------------------------------------- the base interior (grey clone of a Rocket Hideout / Silph Co floor)
def grey(c):
    rr,g,b=[v/31 for v in c]; y=0.30*rr+0.59*g+0.11*b
    return tuple(max(0,min(31,int(round(t*31)))) for t in (y*0.98,y,y*1.03))
STATE=dict(NL=392,NUM=69,grey={})
def grey_secondary(r,S):
    """one shared grey copy of the Hideout / Silph secondary tileset"""
    if S in STATE['grey']: return STATE['grey'][S]
    b=r.b; spal=r32(r,S+8)-0x08000000
    pal=bytearray(b[spal:spal+512])
    for p in range(7,13):
        for i in range(1,16):
            v=struct.unpack('<H',pal[32*p+2*i:32*p+2*i+2])[0]
            cr,cg,cb=grey((v&31,(v>>5)&31,(v>>10)&31)); pal[32*p+2*i:32*p+2*i+2]=struct.pack('<H',cr|(cg<<5)|(cb<<10))
    pa=r.alloc(bytes(pal),4)
    H=bytearray(b[S:S+24]); H[8:12]=struct.pack('<I',0x08000000+pa); sec=r.alloc(bytes(H),4)
    STATE['grey'][S]=sec; return sec
def grey_primary(r,P):
    """shared grey copy of the indoor primary tileset (palettes 0-6), so elevator doors, plants and the like are grey too"""
    key=('P',P)
    if key in STATE['grey']: return STATE['grey'][key]
    b=r.b; pp=r32(r,P+8)-0x08000000
    pal=bytearray(b[pp:pp+7*32])
    for p in range(7):
        for i in range(1,16):
            v=struct.unpack('<H',pal[32*p+2*i:32*p+2*i+2])[0]
            cr,cg,cb=grey((v&31,(v>>5)&31,(v>>10)&31)); pal[32*p+2*i:32*p+2*i+2]=struct.pack('<H',cr|(cg<<5)|(cb<<10))
    pa=r.alloc(bytes(pal),4)
    H=bytearray(b[P:P+24]); H[8:12]=struct.pack('<I',0x08000000+pa); new=r.alloc(bytes(H),4)
    STATE['grey'][key]=new; return new
def build_base_map(r,src_n,objects,warps,mapsec,name):
    b=r.b
    src=header(r,1,src_n); slay=r32(r,src)-0x08000000
    S=r32(r,slay+20)-0x08000000
    sec=grey_secondary(r,S)
    lay=bytearray(b[slay:slay+28]); lay[20:24]=struct.pack('<I',0x08000000+sec); assert bytes(lay[24:26])==bytes([2,2]),lay[24:28].hex()
    lay=r.alloc(bytes(lay),4)
    ob=b''.join(bytes(t) for t in objects); oa=r.alloc(ob,4)
    wb=b''.join(struct.pack('<hhBBBB',*w) for w in warps); wa=r.alloc(wb,4)
    ev=r.alloc(bytes([len(objects),len(warps),0,0])+struct.pack('<IIII',0x08000000+oa,0x08000000+wa,0,0),4)
    ms=r.alloc(b'\x00',1)
    hb=bytearray(b[src:src+28]); hb[0:4]=struct.pack('<I',0x08000000+lay); hb[4:8]=struct.pack('<I',0x08000000+ev); hb[8:12]=struct.pack('<I',0x08000000+ms); hb[12:16]=bytes(4)
    LT=r32(r,0x55194)-0x08000000; NL=STATE['NL']
    for k in (383,391): lp=r32(r,LT+4*k)-0x08000000; assert 4<=r32(r,lp)<=60,k
    tab=r.alloc(bytes(b[LT:LT+4*NL])+struct.pack('<I',0x08000000+lay),4); r.w32(0x55194,0x08000000+tab)
    hb[18:20]=struct.pack('<H',NL+1); STATE['NL']=NL+1
    if mapsec not in STATE.setdefault('named',set()): r.w32(0x3f1cac+4*(mapsec-0x58),0x08000000+r.alloc(leg1.enc(name),1)); STATE['named'].add(mapsec)
    hb[20]=mapsec; hb[0x1a]=100; hb[25]|=0x04
    hdr=r.alloc(bytes(hb),4)
    g2=r32(r,GROUPS+8)-0x08000000; num=STATE['NUM']
    for k in (60,num-1): hp=r32(r,g2+4*k)-0x08000000; assert 0x08000000<=r32(r,hp)<0x0a000000,k
    ntab=r.alloc(bytes(b[g2:g2+4*num])+struct.pack('<I',0x08000000+hdr),4); r.w32(GROUPS+8,0x08000000+ntab)
    STATE['NUM']=num+1
    return 2,num
def best_entry(r,src_n):
    """the source warp whose surroundings give the biggest walkable floor: that tile becomes the base's entrance"""
    import reach
    d=bytes(r.b); h=header(r,1,src_n); ev=r32(r,h+4)-0x08000000; wp=r32(r,ev+8)-0x08000000
    ws=[struct.unpack('<hhBBBB',r.b[wp+8*i:wp+8*i+8])[:2] for i in range(r.b[ev+1])]
    best=None
    for w in ws:
        s,_=reach.reach(d,1,src_n,w)
        if best is None or len(s)>len(best[1]): best=(w,s)
    return best[0],ws
# ----------------------------------------------------------------------------------------------- events helpers
def add_coord(r,g,n,x,y,script):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; nc=r.b[ev+2]
    old=b''
    if nc: cp=r32(r,ev+12)-0x08000000; old=bytes(r.b[cp:cp+16*nc])
    new=r.alloc(old+struct.pack('<HHBBHHHI',x,y,3,0,0x40E3,0,0,script),4); r.b[ev+2]=nc+1; r.w32(ev+12,0x08000000+new)   # var 0x40E3 stays 0, so the event always runs (trigger 0 would run the script in the wrong context)
def door_lock_script(r,item,need,name):
    """stepping on the tile in front of the door without the previous base's medal: refused and pushed back"""
    S=SB(); S.lockall()
    S.raw(0x47); S._add(struct.pack('<HH',item,1))                  # checkitem
    S.compare(0x800D,1); S.goto_if(1,'open')
    S.msg(TXT(r,"The door is locked. A plate beside it reads:\n\n%s REQUIRED."%name),4)
    S.applymovement(0xff,0x08000000+r.alloc(bytes([0x10,0xfe]),1)); S.waitmovement(0xff); S.releaseall(); S.end()
    S.lab('open'); S.releaseall(); S.end()
    return 0x08000000+put_script(r,S)
def patrol_tiles(r,g,n,start,keep_out,k=2,seed='p'):
    """two open lawn tiles reachable from `start` for the patrol templates (the native moves them to a random spot at every visit anyway)"""
    import reach,random
    d=bytes(r.b); seen,(w,h)=reach.reach(d,g,n,start)
    _,_,grid,beh,objs=reach.load(d,g,n)
    ok=[p for p in sorted(seen) if 2<=p[0]<w-2 and 2<=p[1]<h-2 and all(((grid[p[1]+j][p[0]+i]>>10)&3)==0 and (grid[p[1]+j][p[0]+i]>>12)==3 for i in (-1,0,1) for j in (-1,0,1))
        and not any(abs(p[0]-a)<=3 and abs(p[1]-b)<=3 for a,b in keep_out)]
    rng=random.Random(seed); rng.shuffle(ok); out=[]
    for p in ok:
        if all(abs(p[0]-q[0])+abs(p[1]-q[1])>=6 for q in out): out.append(p)
        if len(out)==k: break
    assert len(out)==k,'no patrol tiles'
    return out
# ----------------------------------------------------------------------------------------------- exterior sites (all bases use the same grey house, grafted into the town's tileset)
HOUSE=(32,8,5,4)           # Pewter's house (x,y,w,h); door at column 1 of the bottom row
# bx,by = top left of the house; yg = the approach row below it. ground = tile whose block fills cleared land. carve = corridor rectangles, clear = open land, guards = (x,y,facing), start = a tile on the existing town road
EXT={
 'SEVEN ISLAND':dict(ext=14,ground=(23,16),carve=[],clear=[],rowfill=[(24,37,14,19,23),(24,37,20,29,23)],bx=28,by=14,guards=[(27,18,10),(33,18,9)],sign=(34,18),start=(21,16)),
 'PALLET':   dict(ext=14,ground=(18,17),carve=[(22,17,36,18)],clear=[(24,12,35,16)],bx=28,by=13,guards=[(27,17,10),(33,17,9)],sign=(34,17),start=(21,17),evac=(12,11)),
 'VIRIDIAN': dict(ext=8, ground=(36,14),carve=[(42,20,52,21)],clear=[(42,15,52,19)],bx=45,by=16,guards=[(44,20,10),(50,20,9)],sign=(51,20),start=(41,20)),
 'CERULEAN': dict(ext=14,ground=(39,14),carve=[],clear=[(48,13,57,17)],bx=50,by=14,guards=[(49,18,10),(55,18,9)],sign=(56,18),start=(46,18)),
 'VERMILION':dict(ext=12,ground=(35,15),carve=[],clear=[(48,13,57,17)],bx=50,by=14,guards=[(49,18,10),(55,18,9)],sign=(56,18),start=(46,18)),
 'LAVENDER': dict(ext=14,ground=(20,13),carve=[(22,13,34,14)],clear=[(24,8,34,12)],bx=27,by=9,guards=[(26,13,10),(32,13,9)],sign=(33,13),start=(21,13)),
 'CELADON':  dict(ext=12,ground=(46,16),carve=[],clear=[(60,7,70,11)],bx=62,by=8,guards=[(61,12,10),(67,12,9)],sign=(68,12),start=(56,13)),
 'SAFFRON':  dict(ext=0, ground=(11,25),carve=[],clear=[],bx=9,by=21,guards=[(10,28,7),(13,26,9)],sign=(9,26),start=(13,27)),
 'FUCHSIA':  dict(ext=0, ground=(34,17),carve=[],clear=[],bx=35,by=13,guards=[(34,17,10),(40,17,9)],sign=(33,17),start=(34,18)),
 'CINNABAR': dict(ext=0, ground=(11,14),carve=[],clear=[],bx=10,by=16,guards=[(9,20,10),(15,20,9)],sign=(16,20),start=(12,13),insert=(15,10,[14])),
}
def carve_exterior(r,c,house):
    """rebuilds the town map for city c: extension, cleared land, the grafted house, tileset; returns door tile, front tile, door warp index placeholder"""
    g,n=3,c['town']; e=EXT[c['name']]
    ts=army_tiles.Tileset(r,g,n)
    gv=army_sites.get_block(r,g,n,*e['ground'])
    if e['ext']: army_sites.extend_right(r,g,n,e['ext'])
    if e.get('insert'): army_sites.insert_rows(r,g,n,*e['insert'])
    pre=army_sites.get_grid(r,g,n)          # the map before any cut (forests are repaired against it)
    rects=list(e['carve'])+list(e['clear'])+[(x0,y0,x1,y1) for (x0,x1,y0,y1,sx) in e.get('rowfill',[])]+[(e['bx'],e['by'],e['bx']+4,e['by']+3)]
    for (x0,y0,x1,y1) in e['carve']+e['clear']: army_sites.fill(r,g,n,x0,y0,x1,y1,gv)
    for (x0,x1,y0,y1,sx) in e.get('rowfill',[]):
        for yy in range(y0,y1+1):
            v=army_sites.get_block(r,g,n,sx,yy)
            for xx in range(x0,x1+1): army_sites.set_block(r,g,n,xx,yy,v)
    if e.get('evac'): ts.evacuate(*e['evac'])
    slot=ts.free_slot(); assert slot,'no free palette slot in '+c['name']
    blocks=house.graft(ts,slot)
    for j,row in enumerate(blocks):
        for i,v in enumerate(row): army_sites.set_block(r,g,n,e['bx']+i,e['by']+j,v)
    # forests: every tree must stay whole (2 wide, 3 tall); anything the cuts clipped is rebuilt or replaced by lawn
    import retree
    w_,h_=army_sites.dims(r,g,n); zone=set()
    for (x0,y0,x1,y1) in rects:
        for yy in range(y0-3,y1+4):
            for xx in range(x0-3,x1+4): zone.add((xx,yy))
    cur=army_sites.get_grid(r,g,n); army_sites.put_grid(r,g,n,retree.retree(cur,pre,w_,h_,gv,zone,ts))
    ts.commit()
def place_lot_objects(r,c,e,fns,gf,item_by_num,cleared,ids,base_num,base_map):
    """door warp, lock, guards, sign, patrols in the town map; returns patrol ids"""
    g,n=3,c['town']; G_SOLDIER,G_CAPTAIN,G_SPLAT=gf; nm=army_text.SURNAMES[8*c['idx']:8*c['idx']+8]
    door=(e['bx']+1,e['by']+3); front=(e['bx']+1,e['by']+4)
    dw=add_warp(r,g,n,door[0],door[1],0,base_num,2)
    if c['num']>1: add_coord(r,g,n,front[0],front[1],door_lock_script(r,item_by_num[c['num']-1],c['num']-1,[x for x in CITIES if x['num']==c['num']-1][0]['medal_full']))
    guard_ids,pat_ids=ids[7:9],ids[5:7]
    for k,(gx,gy,mv) in enumerate(e['guards']):
        a,b,cc=army_text.lines('guard',guard_ids[k],c['name'],c['num'],c['captain'])
        make_trainer(r,guard_ids[k],CLS_SOLDIER,PIC_SOLDIER,nm[6+k],gen_team(c,'soldier',guard_ids[k]))
        add_obj(r,g,n,obj_tmpl(G_SOLDIER,gx,gy,soldier_script(r,guard_ids[k],a,b,cc),mv,1,4,cleared))
    add_sign(r,g,n,e['sign'][0],e['sign'][1],0x3402,"JOHTO REVOLUTIONARY ARMY\nBASE NO. %d\n%s\n\nPEACE THROUGH CONQUEST!"%(c['num'],c['name']))
    return dw,door,front
def install_city(r,fns,gf,c,house,item_by_num):
    import reach
    b=r.b; idx=c['idx']; ids=ID_POOL[IDS_PER_CITY*idx:IDS_PER_CITY*idx+IDS_PER_CITY]
    base_ids,cap_id,pat_ids,guard_ids=ids[0:4],ids[4],ids[5:7],ids[7:9]
    cleared=FLAG_CLEARED0+idx; G_SOLDIER,G_CAPTAIN,G_SPLAT=gf
    nm=army_text.SURNAMES[8*idx:8*idx+8]; g,n=3,c['town']
    medal_name=c['medal_full']
    nxt=[x['name'] for x in CITIES if x['num']==c['num']+1]; nxt=nxt[0] if nxt else None
    # trainers
    for k,tid in enumerate(base_ids): make_trainer(r,tid,CLS_SOLDIER,PIC_SOLDIER,nm[k],gen_team(c,'soldier',tid))
    make_trainer(r,cap_id,CLS_CAPTAIN,PIC_CAPTAIN,c['captain'],gen_team(c,'captain',cap_id))
    for k,tid in enumerate(pat_ids): make_trainer(r,tid,CLS_SOLDIER,PIC_SOLDIER,nm[4+k],gen_team(c,'soldier',tid))
    base_sc=[soldier_script(r,base_ids[i],*army_text.lines('base',base_ids[i],c['name'],c['num'],c['captain'])) for i in range(4)]
    ci,cd,cw,ca=army_text.captain_lines(c['name'],c['captain'],c['num'],nxt,c['medal_full'])
    cap_sc=captain_script(r,cap_id,cleared,c['item'],ci,cd,cw,ca,medal_name,c['name'])
    pat_sc=[soldier_script(r,pat_ids[i],*army_text.lines('pat',pat_ids[i],c['name'],c['num'],c['captain'])) for i in range(2)]
    # interior
    if c['name']=='PEWTER':
        objs=[obj_tmpl(G_SOLDIER,13,4,base_sc[0],8,1,4,cleared),obj_tmpl(G_SOLDIER,9,9,base_sc[1],10,1,4,cleared),
              obj_tmpl(G_SOLDIER,14,15,base_sc[2],8,1,4,cleared),obj_tmpl(G_SOLDIER,25,17,base_sc[3],9,1,4,cleared),
              obj_tmpl(G_CAPTAIN,24,26,cap_sc,9,1,4,cleared)]
        entry=(12,2); warps_src=[(12,2)]
    else:
        entry,warps_src=best_entry(r,c['src'])
        sold,cap=army_sites.plan_interior(bytes(r.b),1,c['src'],entry,warps_src,4,c['name'])
        objs=[obj_tmpl(G_SOLDIER,p[0],p[1],base_sc[i],mv,1,4,cleared) for i,(p,mv) in enumerate(sold)]+[obj_tmpl(G_CAPTAIN,cap[0][0],cap[0][1],cap_sc,cap[1],1,4,cleared)]
    for i,t in enumerate(objs): t[0]=i+1
    # town door warp index is known before the map: it is the next warp index of the town
    ph=header(r,g,n); pev=r32(r,ph+4)-0x08000000; DW=r.b[pev+1]
    bg,bn=build_base_map(r,c['src'],objs,[(entry[0],entry[1],0,DW,n,g)],0xab,'JRA MILITARY BASE')
    # the town
    e=EXT.get(c['name'])
    if c['name']=='PEWTER':
        ts=army_tiles.Tileset(r,3,2); slot=ts.free_slot(); blocks=house.graft(ts,slot)
        for j,row in enumerate(blocks):
            for i,v in enumerate(row): army_sites.set_block(r,3,2,33+i,2+j,v)
        army_tiles.recolor_brown(ts,[8,9]); ts.commit()
        e=dict(bx=33,by=2,guards=[(33,6,10),(38,6,9)],sign=(39,6),start=(24,36))
    else:
        carve_exterior(r,c,house)
    dw,door,front=place_lot_objects(r,c,e,None,gf,item_by_num,cleared,ids,bn,bg)
    assert dw==DW,(dw,DW)
    keep=[door,front,e['sign']]+[(x,y) for x,y,_ in e['guards']]
    if c['name']=='PEWTER': pts=[(27,22),(30,15)]
    else: pts=patrol_tiles(r,g,n,e['start'],keep,2,c['name'])
    for sc,pos in zip(pat_sc,pts): add_obj(r,g,n,obj_tmpl(G_SOLDIER,pos[0],pos[1],sc,1,1,4,cleared))
    # reachability
    seen,_=reach.reach(bytes(r.b),bg,bn,entry)
    for t in objs:
        x,y=struct.unpack('<hh',bytes(t[4:8])); assert any((x+dx,y+dy) in seen for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))),('base object not reachable',c['name'],x,y)
    seen,_=reach.reach(bytes(r.b),g,n,e['start'])
    assert front in seen,('base door not reachable',c['name'],front)
    if e.get('ext'):
        W,_=army_sites.dims(r,g,n)
        assert any((W-1,yy) in seen for yy in range(0,40)) or c['name'] in ('PALLET','VIRIDIAN','LAVENDER','SAFFRON'),'east exit lost'
    return dict(pat_ids=pat_ids,cleared=cleared,victims=VICTIM_VARS[idx])

def flag_lock_script(r,flag,text):
    """the camp door: refused (and pushed back) until the flag is set"""
    S=SB(); S.lockall()
    S.raw(0x2b); S._add(struct.pack('<H',flag)); S.goto_if(1,'open')
    S.msg(TXT(r,text),4)
    S.applymovement(0xff,0x08000000+r.alloc(bytes([0x10,0xfe]),1)); S.waitmovement(0xff); S.releaseall(); S.end()
    S.lab('open'); S.releaseall(); S.end()
    return 0x08000000+put_script(r,S)
def general_script(r,tid,flag_cleared):
    L=army_text.GENERAL_LINES
    S=SB(); S.raw(0x5c,1); S._add(struct.pack('<HH',tid,0)); S.ptr(TXB(r,L['intro'])); S.ptr(TXB(r,L['defeat'])); S.ref('cont')
    S.msg(TXT(r,L['after']),6); S.end()
    S.lab('cont')
    S.raw(0x2b); S._add(struct.pack('<H',flag_cleared)); S.goto_if(1,'again')
    S.setflag(flag_cleared)
    for c_ in CITIES: S.setflag(FLAG_CLEARED0+c_['idx'])             # the army collapses: every patrol and base soldier leaves
    S.raw(0x44); S._add(struct.pack('<HH',68,5))                     # 5 RARE CANDY
    S.msg(TXT(r,L['won'][0])); S.msg(TXT(r,L['won'][1]))
    S.msg(TXT(r,"You received 5 RARE CANDY!"),4)
    S.msg(TXT(r,L['final']),6); S.end()
    S.lab('again'); S.msg(TXT(r,L['after']),6); S.end()
    return 0x08000000+put_script(r,S)
def install_camp(r,fns,gf,g_general,house,flag_champ):
    import reach
    g,n=3,18; b=r.b; G_SOLDIER,G_CAPTAIN,G_SPLAT=gf
    ids=ID_POOL[GENERAL_ID_SLICE[0]:GENERAL_ID_SLICE[1]]; gen_id,elite=ids[0],ids[1:3]; guard_id=ids[3]
    make_trainer(r,gen_id,CLS_GENERAL,PIC_GENERAL,army_text.GENERAL,[(sp,50) for sp in LEGENDS])
    for tid in elite: make_trainer(r,tid,CLS_SOLDIER,PIC_SOLDIER,'ELITE',camp_team(tid,4,46,49))
    make_trainer(r,guard_id,CLS_SOLDIER,PIC_SOLDIER,'GUARD',camp_team(guard_id,3,44,47))
    # interior: Silph Co 1F, the lobby floor; the General sits in the deepest dead end
    entry,warps_src=best_entry(r,47)
    sold,cap=army_sites.plan_interior(bytes(r.b),1,47,entry,warps_src,4,'CAMP')
    objs=[]
    for i,(p_,mv) in enumerate(sold):
        tid=elite[i//2]; a_,b_,c_=army_text.camp_lines('elite',tid*10+i)
        objs.append(obj_tmpl(G_SOLDIER,p_[0],p_[1],soldier_script(r,tid,a_,b_,c_),mv,1,4,FLAG_GENERAL))
    objs.append(obj_tmpl(g_general,cap[0][0],cap[0][1],general_script(r,gen_id,FLAG_GENERAL),cap[1],1,4,0))
    for i,t in enumerate(objs): t[0]=i+1
    ph=header(r,g,n); pev=r32(r,ph+4)-0x08000000; DW=r.b[pev+1]
    bg,bn=build_base_map(r,47,objs,[(entry[0],entry[1],0,DW,n,g)],0xac,'JRA HEADQUARTERS')
    # the island: same grey house as every base, on an eastern extension
    c=dict(name='SEVEN ISLAND',town=n)
    carve_exterior(r,c,house); e=EXT['SEVEN ISLAND']
    door=(e['bx']+1,e['by']+3); front=(e['bx']+1,e['by']+4)
    dw=add_warp(r,g,n,door[0],door[1],0,bn,2); assert dw==DW
    add_coord(r,g,n,front[0],front[1],flag_lock_script(r,flag_champ,army_text.LOCK_LEAGUE))
    for k,(gx,gy,mv) in enumerate(e['guards']):
        a_,b_,c_=army_text.camp_lines('guard',guard_id*10+k)
        add_obj(r,g,n,obj_tmpl(G_SOLDIER,gx,gy,soldier_script(r,guard_id,a_,b_,c_),mv,1,4,FLAG_GENERAL))
    add_sign(r,g,n,e['sign'][0],e['sign'][1],0x3402,army_text.CAMP_SIGN)
    seen,_=reach.reach(bytes(r.b),bg,bn,entry)
    for t in objs:
        x,y=struct.unpack('<hh',bytes(t[4:8])); assert any((x+dx,y+dy) in seen for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))),('camp object not reachable',x,y)
    seen,_=reach.reach(bytes(r.b),g,n,e['start'])
    assert front in seen,'camp door not reachable'
    return dict(general=gen_id,flag=FLAG_GENERAL)
# ----------------------------------------------------------------------------------------------- main
if __name__=='__main__':
    import qconsts
    r=Rom(sys.argv[1]); b=r.b
    FLAGS,VARS,ITEMS=qconsts.consts()
    g_soldier=army_gfx.add_remapped(r,49,SOLDIER_MAP); g_captain=army_gfx.add_remapped(r,82,CAPTAIN_MAP,fn=captain_frame); g_splat=add_alias_gfx(r,0x98)
    print('gfx',hex(g_soldier),hex(g_captain),hex(g_splat))
    assert (g_soldier,g_captain,g_splat)==(0x9f,0xa0,0xa1)
    surge_pic=b[T+40*416+3]
    pic_from_png(r,PIC_SOLDIER,W+'/soldier_pic.png')          # supplied soldier picture
    alloc_trainer_pic(r,PIC_CAPTAIN,surge_pic,lambda c: ramp(c,'captain'),captain_pupil)
    g_general=army_gfx.add_remapped(r,87,{},fn=make_general_fn()); assert g_general==0xa2
    pic_from_png(r,PIC_GENERAL,W+'/general_pic.png')          # supplied General picture
    rename_class(r,CLS_SOLDIER,'JRA SOLDIER'); rename_class(r,CLS_CAPTAIN,'JRA CAPTAIN'); rename_class(r,CLS_GENERAL,'JRA GENERAL')
    item_by_num={}
    for c in CITIES:
        add_medal(r,c['item'],c['medal'],c['medal_desc'],ITEMS['ITEM_OLD_AMBER']); item_by_num[c['num']]=c['item']
    # collision: the army splatter never blocks (same exemption as the player's splatter and story bodies)
    code=r.asm('ldrb r0,[r2,#5]\ncmp r0,#%d\nbeq exempt\nsubs r0,#0x98\ncmp r0,#1\nbhi normal\nexempt:\nldr r0,=0x0806396d\nbx r0\nnormal:\nldrb r0,[r6,#0xb]\nlsls r0,r0,#0x1c\nbx lr\n'%g_splat,0x3b2300)
    r.put(0x3b2300,code)
    h1,h2=struct.unpack('<HH',b[0x6394c:0x63950]); off=((h1&0x7FF)<<12)|((h2&0x7FF)<<1)
    assert 0x6394c+4+off==0x3af2b8
    r.bl(0x6394c,0x3b2300)
    # natives: the army splat script address lives in a ROM slot written after the script exists (breaks the script <-> native address cycle)
    slot=r.alloc(b'\xff'*4,4); old_apply=r32(r,0xa09824)
    pat=[]
    for c in CITIES:
        for tid in ID_POOL[IDS_PER_CITY*c['idx']+5:IDS_PER_CITY*c['idx']+7]: pat.append((tid,FLAG_CLEARED0+c['idx'],VICTIM_VARS[c['idx']]))
    reasons=[etxt(s_) for s_ in REASONS]
    h='#define GFX_SOLDIER %d\n#define GFX_ARMY_SPLAT %d\n#define SPLAT_SLOT 0x%08x\n#define OLD_APPLY 0x%08x\n#define MAX_VICTIMS %d\n'%(g_soldier,g_splat,0x08000000+slot,old_apply,MAX_VICTIMS)
    h+='#define NPAT %d\nstatic const unsigned short PAT_ID[]={%s};\nstatic const unsigned short PAT_CLEARED[]={%s};\nstatic const unsigned short PAT_VICTIMS[]={%s};\n'%(len(pat),','.join(str(p_[0]) for p_ in pat),','.join(str(p_[1]) for p_ in pat),','.join(str(p_[2]) for p_ in pat))
    h+='#define NREASONS %d\n'%len(reasons)+''.join('static const unsigned char R%d[]={%s};\n'%(i_,','.join(map(str,x))) for i_,x in enumerate(reasons))+'static const unsigned char* const REASONS[]={%s};\n'%','.join('R%d'%i_ for i_ in range(len(reasons)))
    fns=build_native(r,h)
    r.w32(slot,splat_script(r,fns))
    # the grey house, read from Pewter's original tileset before anything is recoloured
    house=army_tiles.House(army_tiles.Tileset(r,3,2),HOUSE)
    order=[c for c in CITIES if c['name']=='PEWTER']+[c for c in CITIES if c['name']!='PEWTER']
    for c in order:
        info=install_city(r,fns,(g_soldier,g_captain,g_splat),c,house,item_by_num)
        print('installed',c['name'],'base map',STATE['NUM']-1,'ids',info['pat_ids'])
    camp=install_camp(r,fns,(g_soldier,g_captain,g_splat),g_general,house,FLAGS['FLAG_DEFEATED_CHAMP'])
    print('camp',camp)
    json.dump([dict(name=c['name'],num=c['num'],idx=c['idx'],captain=c['captain'],flag=FLAG_CLEARED0+c['idx'],item=c['item'],cap=c['cap'],medal=c['medal_full']) for c in CITIES]+[dict(name='GENERAL',num=11,idx=10,captain=army_text.GENERAL,flag=FLAG_GENERAL,item=0,cap=50,medal='')],open(W+'/cities.json','w'))
    # hook: the map-load pass now runs the old one (police, shot trainers) and then the army pass
    assert b[0xa0981c:0xa09824]==bytes.fromhex('014b1847c046c046')
    r.w32(0xa09824,fns['army_entry'])
    r.save(sys.argv[2]); print('ok end',hex(r.cur))
