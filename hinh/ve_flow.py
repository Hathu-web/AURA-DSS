import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Ellipse
plt.rcParams["font.family"]="DejaVu Sans"
W,H=20,15.5; fig,ax=plt.subplots(figsize=(W,H),dpi=150); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
FS=15; FST=17
C={"src":("#fde2f3","#c2185b"),"proc":("#e3f2fd","#1565c0"),"db":("#fff8e1","#f9a825"),"ml":("#e8f5e9","#2e7d32"),"out":("#ede7f6","#4527a0")}
def band(y0,y1,title,col):
    ax.add_patch(FancyBboxPatch((0.4,y0),W-0.8,y1-y0,boxstyle="round,pad=0.02,rounding_size=0.25",fc=col[0],ec=col[1],lw=1.2,alpha=0.35,zorder=0))
    ax.text(0.7,y1-0.12,title,fontsize=FST,fontweight="bold",va="top",ha="left",color="#263238")
def box(x,y,w,h,txt,k,shape="box"):
    f,e=C[k]
    if shape=="box": ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle="round,pad=0.02,rounding_size=0.15",fc=f,ec=e,lw=2,zorder=2))
    elif shape=="dia": ax.add_patch(Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],fc=f,ec=e,lw=2,zorder=2))
    elif shape=="cyl":
        ax.add_patch(FancyBboxPatch((x-w/2,y-h/2+0.15),w,h-0.3,boxstyle="square,pad=0",fc=f,ec=e,lw=2,zorder=2))
        ax.add_patch(Ellipse((x,y-h/2+0.15),w,0.3,fc=f,ec=e,lw=2,zorder=2)); ax.add_patch(Ellipse((x,y+h/2-0.15),w,0.3,fc=f,ec=e,lw=2,zorder=3))
    ax.text(x,y,txt,ha="center",va="center",fontsize=FS,zorder=4,linespacing=1.35)
    return (x,y,w,h)
def arr(a,b,lab=None,dx=0,style="-|>",off=(0,0)):
    x1,y1,w1,h1=a; x2,y2,w2,h2=b
    p1=(x1+dx, y1-h1/2 if y2<y1 else y1+h1/2) if abs(y1-y2)>0.5 else (x1+w1/2 if x2>x1 else x1-w1/2, y1)
    p2=(x2, y2+h2/2 if y2<y1 else y2-h2/2) if abs(y1-y2)>0.5 else (x2-w2/2 if x2>x1 else x2+w2/2, y2)
    ax.add_patch(FancyArrowPatch(p1,p2,arrowstyle=style,mutation_scale=22,lw=2,color="#37474f",connectionstyle="arc3,rad=0.0",zorder=1))
    if lab: ax.text((p1[0]+p2[0])/2+off[0],(p1[1]+p2[1])/2+off[1],lab,fontsize=FS,ha="center",va="center",bbox=dict(fc="white",ec="none",pad=1),zorder=5)

# ① nguồn
band(13.4,15.3,"① Nguồn dữ liệu – Kaggle Home Credit (4 bảng CSV)",C["src"])
A=box(3,13.95,4.3,1.0,"application_train.csv\n307.511 dòng × 122 cột","src")
B=box(7.7,13.95,4.0,1.0,"bureau.csv\n1.716.428 dòng","src")
Cc=box(12.3,13.95,4.3,1.0,"previous_application.csv\n1.670.214 dòng","src")
D=box(17,13.95,4.3,1.0,"installments_payments.csv\n13.605.401 dòng","src")
# ② làm sạch
band(10.9,12.9,"② Làm sạch & Tổng hợp (pandas)",C["proc"])
E=box(4.3,11.45,7.2,1.0,"Làm sạch hồ sơ (application)\nXNA · 365243→NULL · inf→NULL · cờ bất thường","proc")
F=box(13.5,11.45,7.6,1.0,"Tổng hợp theo SK_ID_CURR (groupby/agg)\n94 đặc trưng tiền tố bu_ / pv_ / ins_ / ins1y_","proc")
# ③ kho
band(8.4,10.4,"③ Kho dữ liệu (SQLite – 10 bảng, JOIN theo customer_id)",C["db"])
G=box(6,8.95,6.0,1.3,"aura_bnpl.db\nDIM_* · FACT_* · CUSTOMER_SCORE","db","cyl")
Hh=box(13.5,8.95,5.0,1.0,"FEATURE_STORE\n188 đặc trưng / khách hàng","db")
# ④ mô hình
band(5.9,7.9,"④ Mô hình dự báo (LightGBM, 5-fold ensemble)",C["ml"])
R=box(10,6.5,3.2,1.3,"Router\ncó lịch sử?","ml","dia")
M1=box(4.3,6.5,5.0,1.0,"Thick-file FPD model\n188 đặc trưng · AUC 0,790","ml")
M2=box(15.7,6.5,5.0,1.0,"Thin-file FPD model\nchỉ hồ sơ · khách mới","ml")
# ⑤ quyết định
band(2.5,5.4,"⑤ Quyết định & Khuyến nghị",C["ml"])
P=box(10,4.45,7.0,0.8,"P_FPD → Tier (Low/Medium/High) → Hạn mức","ml")
S=box(4.3,3.15,5.6,0.9,"MILP PuLP/CBC – phân bổ vốn theo lô\nquỹ 2 tỷ · trần rủi ro 4%","ml")
X=box(15.7,3.15,5.0,0.9,"SHAP – giải thích từng hồ sơ","ml")
# ⑥ đầu ra
band(0.3,2.0,"⑥ Đầu ra",C["out"])
L=box(4.3,1.0,4.6,0.9,"FACT_DECISION_LOG","db","cyl")
AG=box(15.7,1.0,5.0,0.9,"Agent Gemini\ngiải thích + PrivacyGuard","out")
DB=box(10,1.0,4.0,0.9,"Streamlit Dashboard","out")

arr(A,E); arr(B,F); arr(Cc,F); arr(D,F); arr(E,G); arr(F,G); arr(G,Hh); arr(Hh,R)
arr(R,M1,"có",off=(0,0.3)); arr(R,M2,"không",off=(0,0.3)); arr(M1,P); arr(M2,P)
# P -> S, P -> X (xuống chéo)
for tgt in (S,X):
    ax.add_patch(FancyArrowPatch((P[0]+(-2.5 if tgt is S else 2.5),P[1]-0.4),(tgt[0],tgt[1]+0.45),arrowstyle="-|>",mutation_scale=22,lw=2,color="#37474f",zorder=1))
arr(S,L); arr(X,AG); arr(L,DB); arr(AG,DB)
plt.savefig("flow_aura.png",bbox_inches="tight",facecolor="white"); plt.savefig("flow_aura.svg",bbox_inches="tight",facecolor="white")
