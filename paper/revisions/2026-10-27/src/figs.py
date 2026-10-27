from clip import *

def fig1():
    W,H=195,86
    fig,ax=canvas(W,H)
    pw=43.5; gap=4.7; y=4; h=78
    xs=[3+i*(pw+gap) for i in range(4)]
    cols=[INDIGO,TEAL,TERRA,DGREEN]
    titles=["Data layer","Forecast and storage","Cooperative plan","Approval and WhatsApp"]
    for i,(x,c,t) in enumerate(zip(xs,cols,titles)): panel(ax,x,y,pw,h,t,c,i+1)
    # 1 data
    x=xs[0]
    mandi(ax,x+10,y+58,15); label(ax,x+10,y+46.5,"AGMARKNET\nmandi prices",5.2)
    farmer(ax,x+33,y+60,13); label(ax,x+33,y+46.5,"FPO members\nand lots",5.2)
    esp32(ax,x+10,y+31,15); probe(ax,x+19,y+31,12); label(ax,x+14.5,y+19.5,"ESP32 + SHT30\ngrain sensor",5.2)
    sack(ax,x+33,y+31,12); label(ax,x+33,y+19.5,"Stock in\nstorage",5.2)
    rbox(ax,x+4,y+4,pw-8,9,LGREY,ec=INDIGO,lw=.8); label(ax,x+pw/2,y+8.5,"Cleaning and checks",5.2,bold=True)
    # 2 forecast
    x=xs[1]
    diamond(ax,x+pw/2,y+57,34,16,SAND,"MSP or\nmarket price?",5.2)
    label(ax,x+8,y+45,"MSP crop:\nfixed price",4.9,TEAL,bold=True); label(ax,x+pw-8.5,y+45,"Basmati:\nforecast",4.9,TERRA,bold=True)
    chart(ax,x+pw-13,y+31,17); label(ax,x+pw-13,y+19.5,"price forecast",5.0)
    sack(ax,x+11,y+31,11,grain=True); wifi(ax,x+19,y+34,5); label(ax,x+11,y+19.5,"storage risk\nlow / medium / high",4.8)
    rbox(ax,x+4,y+4,pw-8,9,LGREY,ec=TEAL,lw=.8); label(ax,x+pw/2,y+8.5,"Hold-or-sell advice",5.2,bold=True)
    # 3 plan
    x=xs[2]
    scale(ax,x+12,y+57,16); label(ax,x+12,y+46,"shared daily\nlimits",5.0)
    truck(ax,x+33,y+57,17); label(ax,x+33,y+46,"mandi, day,\nquantity",5.0)
    graph(ax,x+pw/2,y+31,20,TERRA); label(ax,x+pw/2,y+19.5,"integer program + plan check",4.8)
    rbox(ax,x+4,y+4,pw-8,9,LGREY,ec=TERRA,lw=.8); label(ax,x+pw/2,y+8.5,"Draft plan",5.2,bold=True)
    # 4 approval
    x=xs[3]
    laptop(ax,x+12,y+57,17); label(ax,x+12,y+46,"manager checks\nand approves",5.0)
    tick(ax,x+22,y+63,6)
    phone(ax,x+33,y+56,17); label(ax,x+33,y+44.5,"WhatsApp\nPA / HI / EN",5.0)
    farmer(ax,x+12,y+32,14,shirt=BLUE); farmer(ax,x+26,y+32,14,shirt=GREEN,turban=INDIGO)
    label(ax,x+19,y+19.5,"members sell,\nsale recorded",4.8)
    rbox(ax,x+4,y+4,pw-8,9,LGREY,ec=DGREEN,lw=.8); label(ax,x+pw/2,y+8.5,"Stock update, next plan",5.2,bold=True)
    for i in range(3): arrow(ax,(xs[i]+pw+.4,y+h/2),(xs[i+1]-.4,y+h/2),INK,2,ms=11)
    save(fig,"../figs/fig1_architecture.png")

def fig2():
    W,H=190,60
    fig,ax=canvas(W,H)
    steps=[("Raw price\nfiles",lambda x,y:chart(ax,x,y,14,band=False),INDIGO),
           ("Clean and\ncheck",lambda x,y:gear(ax,x,y,12,GREY),GREY),
           ("MSP\ncheck",lambda x,y:scale(ax,x,y,13),TERRA),
           ("Mandi\ngraph",lambda x,y:graph(ax,x,y,15),INDIGO),
           ("Graph conv.\n+ GRU",lambda x,y:gear(ax,x,y,12,TEAL),TEAL),
           ("Attention\nover 7 days",lambda x,y:chart(ax,x,y,14,seed=4),TERRA),
           ("Price\nforecast",lambda x,y:tick(ax,x,y,10),DGREEN)]
    n=len(steps); bw=23; gap=(W-6-n*bw)/(n-1)
    for i,(t,ic,c) in enumerate(steps):
        x=3+i*(bw+gap)
        rbox(ax,x,10,bw,40,PAPER,ec=c,lw=1.5,r=3)
        rbox(ax,x,41,bw,9,c,ec=c,r=3); ax.add_patch(Rectangle((x+.8,41),bw-1.6,3,fc=c,zorder=2))
        label(ax,x+bw/2,45.5,str(i+1),7,"white",bold=True)
        ic(x+bw/2,28)
        label(ax,x+bw/2,16,t,5.4,bold=True)
        if i<n-1: arrow(ax,(x+bw+.3,30),(x+bw+gap-.3,30),INK,1.6,ms=9)
    label(ax,W/2,4.5,"Input: last 7 prices of every mandi, scaled by the latest price      Output: relative change for the next 1–7 trading dates",5.4,MUTED:="#5A6678")
    save(fig,"../figs/fig_method.png")

def fig3():
    W,H=195,72
    fig,ax=canvas(W,H)
    rbox(ax,3,3,92,66,"#F7EFD8",ec=TERRA,lw=1.6,r=3)
    label(ax,49,64,"Grain container (labelled lot)",6.5,TERRA,bold=True)
    ax.add_patch(Polygon([(8,8),(90,8),(90,32),(8,32)],fc="#EBD58A",ec=INK,lw=.9,zorder=1))
    for i in range(11): ax.add_patch(Ellipse((13+i*7.3,13+(i%3)*3),5,2.2,fc="#C9A94A",ec="none",zorder=2))
    probe(ax,24,31,22); label(ax,24,50,"SHT30 probe\nin the grain",5.3)
    esp32(ax,66,50,24); label(ax,66,37.5,"ESP32-WROOM-32\nSDA 21, SCL 22",5.0)
    ax.plot([24,24,52],[40,46,48],color=GREEN,lw=1.6,zorder=5)
    wifi(ax,84,56,8); label(ax,84,48.5,"Wi-Fi",5.0,TEAL)
    cloud(ax,116,54,22); label(ax,116,54,"MQTT\nbroker (TLS)",5.0,bold=True)
    arrow(ax,(90,57),(104,55),TEAL,1.6)
    rbox(ax,104,22,26,16,SKY,ec=BLUE,r=2); label(ax,117,33,"Ingestion",5.6,bold=True); label(ax,117,26.5,"dedupe, store",5.0)
    arrow(ax,(116,43),(116,39),INK,1.4)
    laptop(ax,152,52,22); label(ax,152,38,"Dashboard: 24 h median,\nrisk LOW / MEDIUM / HIGH",4.8)
    arrow(ax,(131,34),(142,44),INK,1.4)
    phone(ax,183,52,20); label(ax,183,38,"WhatsApp alert\nto manager",4.8)
    arrow(ax,(131,26),(183,31),INK,1.4,rad=.1)
    rbox(ax,104,5,88,10,LGREY,ec=GREY,lw=.8); label(ax,148,10,"Wokwi twin runs the same firmware: anyone can reproduce it",5.2,bold=True)
    save(fig,"../figs/fig_node.png")

fig1(); fig2(); fig3(); print("done")
