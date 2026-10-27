"""Flat clipart drawing helpers (matplotlib patches, data units = mm-like)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (FancyBboxPatch, Rectangle, Circle, Polygon, Ellipse, Wedge, FancyArrowPatch, Arc)
import numpy as np

INK="#243044"; INDIGO="#373C7A"; TEAL="#167170"; TERRA="#CA7644"; GREEN="#5FAE6B"; SAND="#ECD781"
SKY="#CFE8F3"; PAPER="#FFF9E8"; RED="#D1495B"; GREY="#9AA5B1"; LGREY="#E6EAF0"; WHITE="#FFFFFF"; SKIN="#E0A878"; BLUE="#3A7CC1"; DGREEN="#2F7D4F"

def canvas(w,h,figw=7.0):
    fig=plt.figure(figsize=(figw,figw*h/w),dpi=300)
    ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,w); ax.set_ylim(0,h); ax.set_aspect("equal"); ax.axis("off")
    return fig,ax

def rbox(ax,x,y,w,h,fc,ec=INK,lw=1.0,r=2.0,z=1,alpha=1):
    p=FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",fc=fc,ec=ec,lw=lw,zorder=z,alpha=alpha); ax.add_patch(p); return p

def panel(ax,x,y,w,h,title,color,num=None):
    rbox(ax,x,y,w,h,PAPER,ec=color,lw=1.6,r=3,z=1)
    rbox(ax,x,y+h-7.5,w,7.5,color,ec=color,lw=1.6,r=3,z=2)
    ax.add_patch(Rectangle((x+0.8,y+h-7.5),w-1.6,3,fc=color,ec=color,lw=0,zorder=2))
    t=(f"{num}  " if num else "")+title
    ax.text(x+w/2,y+h-3.9,t,ha="center",va="center",color="white",fontsize=7.3,fontweight="bold",zorder=5)

def label(ax,x,y,s,size=5.6,color=INK,ha="center",bold=False,z=6,va="center"):
    ax.text(x,y,s,ha=ha,va=va,fontsize=size,color=color,fontweight="bold" if bold else "normal",zorder=z,linespacing=1.15)

def arrow(ax,p,q,color=INK,lw=1.6,rad=0,style="-|>",z=7,ms=9):
    a=FancyArrowPatch(p,q,arrowstyle=style,mutation_scale=ms,lw=lw,color=color,connectionstyle=f"arc3,rad={rad}",zorder=z); ax.add_patch(a)

def badge(ax,x,y,n,color=TERRA):
    ax.add_patch(Circle((x,y),2.4,fc=color,ec="white",lw=1,zorder=8)); label(ax,x,y-0.1,str(n),6.5,"white",bold=True,z=9)

# ---------- icons (x,y = centre, s = scale ~ icon height in units)
def farmer(ax,x,y,s=14,shirt=GREEN,turban=TERRA):
    ax.add_patch(Ellipse((x,y-s*0.42),s*0.75,s*0.5,fc=shirt,ec=INK,lw=0.7,zorder=4))
    ax.add_patch(Circle((x,y+s*0.02),s*0.2,fc=SKIN,ec=INK,lw=0.7,zorder=5))
    ax.add_patch(Wedge((x,y+s*0.08),s*0.23,0,180,fc=turban,ec=INK,lw=0.7,zorder=6))
    ax.add_patch(Circle((x-s*0.07,y+s*0.02),s*0.02,fc=INK,zorder=7)); ax.add_patch(Circle((x+s*0.07,y+s*0.02),s*0.02,fc=INK,zorder=7))
    ax.add_patch(Arc((x,y-s*0.03),s*0.14,s*0.08,theta1=200,theta2=340,color=INK,lw=0.6,zorder=7))

def sack(ax,x,y,s=12,color=SAND,grain=True):
    ax.add_patch(Polygon([(x-s*.4,y-s*.5),(x+s*.4,y-s*.5),(x+s*.45,y+s*.15),(x+s*.2,y+s*.4),(x-s*.2,y+s*.4),(x-s*.45,y+s*.15)],fc=color,ec=INK,lw=0.8,zorder=4))
    ax.add_patch(Polygon([(x-s*.2,y+s*.4),(x-s*.28,y+s*.55),(x+s*.28,y+s*.55),(x+s*.2,y+s*.4)],fc=TERRA,ec=INK,lw=0.8,zorder=4))
    if grain:
        for dx,dy in [(-.15,-.1),(.1,-.2),(0,.1),(-.2,.15),(.2,0)]:
            ax.add_patch(Ellipse((x+dx*s,y+dy*s),s*.09,s*.04,angle=30,fc="#B99A3E",ec="none",zorder=5))

def mandi(ax,x,y,s=16,roof=TERRA):
    ax.add_patch(Rectangle((x-s*.5,y-s*.4),s,s*.5,fc="#F4E6C4",ec=INK,lw=0.8,zorder=4))
    ax.add_patch(Polygon([(x-s*.58,y+s*.1),(x+s*.58,y+s*.1),(x,y+s*.5)],fc=roof,ec=INK,lw=0.8,zorder=5))
    for i in (-.3,0,.3): ax.add_patch(Rectangle((x+i*s-s*.05,y-s*.4),s*.1,s*.5,fc=WHITE,ec=INK,lw=0.5,zorder=5))
    ax.add_patch(Rectangle((x-s*.07,y-s*.4),s*.14,s*.2,fc=INDIGO,ec=INK,lw=0.5,zorder=6))

def truck(ax,x,y,s=18,color=BLUE):
    ax.add_patch(Rectangle((x-s*.5,y-s*.2),s*.65,s*.4,fc=color,ec=INK,lw=0.8,zorder=4))
    ax.add_patch(Polygon([(x+s*.15,y-s*.2),(x+s*.15,y+s*.2),(x+s*.35,y+s*.2),(x+s*.5,y),(x+s*.5,y-s*.2)],fc=SAND,ec=INK,lw=0.8,zorder=4))
    for cx in (-.3,.3): ax.add_patch(Circle((x+cx*s,y-s*.22),s*.09,fc=INK,ec="white",lw=0.6,zorder=6))

def phone(ax,x,y,s=18,msgs=True):
    w=s*.5
    rbox(ax,x-w/2,y-s/2,w,s,INK,ec=INK,lw=0.8,r=1.5,z=4)
    ax.add_patch(Rectangle((x-w/2+.8,y-s/2+2),w-1.6,s-4.2,fc="#E7F6E7",ec="none",zorder=5))
    for i,(dx,col) in enumerate([(-.7,"white"),(.7,"#C8F0C0"),(-.7,"white")]):
        rbox(ax,x-w/2+1.6+max(dx,0)*1.5,y+s*.22-i*s*.22,w*.6,s*.14,col,ec=GREEN,lw=0.4,r=.8,z=6)

def laptop(ax,x,y,s=18):
    rbox(ax,x-s*.4,y-s*.1,s*.8,s*.5,INK,ec=INK,lw=.7,r=1,z=4)
    ax.add_patch(Rectangle((x-s*.35,y-s*.05),s*.7,s*.4,fc=SKY,ec="none",zorder=5))
    ax.add_patch(Polygon([(x-s*.5,y-s*.1),(x+s*.5,y-s*.1),(x+s*.42,y-s*.22),(x-s*.42,y-s*.22)],fc=GREY,ec=INK,lw=.7,zorder=4))
    xs=np.linspace(x-s*.3,x+s*.3,5); ys=y+s*.05+np.array([0,.08,.03,.15,.2])*s
    ax.plot(xs,ys,color=TEAL,lw=1.2,zorder=6)
    ax.add_patch(Rectangle((x-s*.3,y+s*.05),s*.6,s*.02,fc=GREY,zorder=5))

def cloud(ax,x,y,s=16,color=SKY):
    for dx,dy,r in [(-.25,0,.22),(0,.1,.28),(.25,0,.22),(.0,-.06,.25)]:
        ax.add_patch(Circle((x+dx*s,y+dy*s),r*s,fc=color,ec=INK,lw=.7,zorder=4))
    ax.add_patch(Rectangle((x-.35*s,y-.2*s),.7*s,.17*s,fc=color,ec="none",zorder=5))

def esp32(ax,x,y,s=18):
    rbox(ax,x-s*.5,y-s*.3,s,s*.6,"#1F6B4A",ec=INK,lw=.8,r=1,z=4)
    ax.add_patch(Rectangle((x-s*.1,y-s*.12),s*.3,s*.24,fc=INK,ec=GREY,lw=.5,zorder=5))
    ax.add_patch(Rectangle((x-s*.48,y-s*.12),s*.22,s*.24,fc="#D8DCE2",ec=INK,lw=.5,zorder=5))
    xs=np.linspace(x+s*.25,x+s*.45,5)
    ax.plot(xs,[y+s*.22,y+s*.14,y+s*.22,y+s*.14,y+s*.22],color=SAND,lw=.8,zorder=6)
    for i in np.linspace(-.4,.4,7):
        ax.add_patch(Rectangle((x+i*s-s*.015,y+s*.3),s*.03,s*.06,fc=SAND,zorder=3)); ax.add_patch(Rectangle((x+i*s-s*.015,y-s*.36),s*.03,s*.06,fc=SAND,zorder=3))

def probe(ax,x,y,s=18):
    ax.add_patch(Rectangle((x-s*.04,y-s*.5),s*.08,s*.7,fc=GREY,ec=INK,lw=.6,zorder=5))
    rbox(ax,x-s*.1,y+s*.2,s*.2,s*.22,"#2B3A67",ec=INK,lw=.6,r=.8,z=5)
    for i in (-.04,.04): ax.add_patch(Rectangle((x+i*s-.3,y+s*.42),.6,s*.12,fc=SAND,zorder=4))
    ax.add_patch(Polygon([(x-s*.04,y-s*.5),(x+s*.04,y-s*.5),(x,y-s*.6)],fc=GREY,ec=INK,lw=.5,zorder=5))

def wifi(ax,x,y,s=8,color=TEAL):
    for r in (.35,.65,1.0): ax.add_patch(Arc((x,y),r*s,r*s,theta1=45,theta2=135,color=color,lw=1.1,zorder=6))
    ax.add_patch(Circle((x,y),.07*s,fc=color,zorder=6))

def chart(ax,x,y,s=18,color=TEAL,band=True,seed=1):
    ax.add_patch(Rectangle((x-s*.5,y-s*.35),s,s*.7,fc="white",ec=INK,lw=.7,zorder=4))
    xs=np.linspace(x-s*.42,x+s*.42,9); rng=np.random.RandomState(seed); base=y+np.cumsum(rng.randn(9))*s*.03
    if band: ax.fill_between(xs[4:],base[4:]-s*.1,base[4:]+s*.1,color=SAND,alpha=.8,zorder=5,lw=0)
    ax.plot(xs,base,color=color,lw=1.3,zorder=6); ax.plot(xs[4:],base[4:],color=TERRA,lw=1.3,ls="--",zorder=6)

def graph(ax,x,y,s=18,color=INDIGO):
    pts=[(-.35,-.2),(-.1,.3),(.3,.25),(.35,-.2),(0,-.35)]
    P=[(x+a*s,y+b*s) for a,b in pts]
    for i,j in [(0,1),(1,2),(2,3),(3,4),(4,0),(1,4),(1,3)]: ax.plot([P[i][0],P[j][0]],[P[i][1],P[j][1]],color=GREY,lw=.9,zorder=4)
    for k,(px,py) in enumerate(P): ax.add_patch(Circle((px,py),s*.09,fc=[TERRA,color,color,TERRA,color][k],ec=INK,lw=.5,zorder=5))

def gear(ax,x,y,s=14,color=GREY):
    for a in range(0,360,45):
        t=np.deg2rad(a); ax.add_patch(Circle((x+np.cos(t)*s*.4,y+np.sin(t)*s*.4),s*.1,fc=color,ec=INK,lw=.4,zorder=4))
    ax.add_patch(Circle((x,y),s*.38,fc=color,ec=INK,lw=.7,zorder=5)); ax.add_patch(Circle((x,y),s*.15,fc="white",ec=INK,lw=.5,zorder=6))

def tick(ax,x,y,s=8,color=GREEN):
    ax.add_patch(Circle((x,y),s/2,fc=color,ec="white",lw=1,zorder=6))
    ax.plot([x-s*.22,x-s*.05,x+s*.25],[y,y-s*.2,y+s*.2],color="white",lw=1.8,zorder=7,solid_capstyle="round")

def scale(ax,x,y,s=16):
    ax.plot([x,x],[y-s*.4,y+s*.35],color=INK,lw=1.2,zorder=5); ax.plot([x-s*.4,x+s*.4],[y+s*.3,y+s*.3],color=INK,lw=1.2,zorder=5)
    for dx in (-.4,.4):
        ax.add_patch(Polygon([(x+dx*s,y+s*.3),(x+dx*s-s*.18,y),(x+dx*s+s*.18,y)],fc=SAND,ec=INK,lw=.6,zorder=5))
    ax.add_patch(Rectangle((x-s*.2,y-s*.45),s*.4,s*.06,fc=INK,zorder=5))

def diamond(ax,x,y,w,h,fc,txt,size=5.6):
    ax.add_patch(Polygon([(x,y+h/2),(x+w/2,y),(x,y-h/2),(x-w/2,y)],fc=fc,ec=INK,lw=.9,zorder=4)); label(ax,x,y,txt,size,bold=True)

def save(fig,name):
    fig.savefig(name,dpi=300,facecolor="white"); plt.close(fig)
