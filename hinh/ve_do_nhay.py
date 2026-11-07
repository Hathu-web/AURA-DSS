import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
plt.rcParams["font.family"]="DejaVu Sans"
tran=["2%","3%","4%","5%","6%","∞"]; x=np.arange(6)
duyet=[40.8,63.1,66.0,66.0,66.0,66.0]; von=[58.65,89.35,94.25,94.25,94.25,94.25]
nx_du=[2.00,3.00,3.18,3.18,3.18,3.18]; nx_that=[0.85,2.63,3.42,3.42,3.42,3.42]
ln_kv=[35.08,42.85,43.04,43.04,43.04,43.04]
fig,ax=plt.subplots(1,2,figsize=(16,6.2),dpi=150)
# trái: cột duyệt & vốn, đường lợi nhuận
a=ax[0]; w=0.38
a.bar(x-w/2,duyet,w,color="#90caf9",label="Tỷ lệ đơn duyệt (%)")
a.bar(x+w/2,von,w,color="#ffcc80",label="Tỷ lệ vốn sử dụng (%)")
a.set_ylim(0,110); a.set_xticks(x); a.set_xticklabels(tran,fontsize=13); a.set_xlabel("Trần nợ xấu danh mục (r)",fontsize=13)
a.set_ylabel("%",fontsize=13); a.tick_params(labelsize=12)
a2=a.twinx(); a2.plot(x,ln_kv,"o-",color="#c62828",lw=2.5,ms=8,label="Lợi nhuận kỳ vọng (triệu/lô)")
a2.set_ylim(30,46); a2.set_ylabel("triệu VNĐ",fontsize=13,color="#c62828"); a2.tick_params(labelsize=12,colors="#c62828")
for i,v in enumerate(ln_kv): a2.annotate(f"{v:.1f}",(i,v),textcoords="offset points",xytext=(0,9),ha="center",fontsize=11,color="#c62828")
a.axvspan(1.5,5.5,color="#e8f5e9",zorder=0); a.text(3.5,104,"Vùng bão hoà: lời giải không đổi",ha="center",fontsize=12,color="#2e7d32")
a.axvline(2,color="#2e7d32",ls="--",lw=1.5); a.text(2.08,2,"mặc định 4%",fontsize=11,color="#2e7d32",fontweight="bold")
h1,l1=a.get_legend_handles_labels(); h2,l2=a2.get_legend_handles_labels(); a.legend(h1+h2,l1+l2,loc="lower right",fontsize=11)
a.set_title("(a) Đánh đổi: trần chặt → bỏ đơn tốt, vốn nằm im",fontsize=14)
# phải: nợ xấu
b=ax[1]
b.plot(x,nx_du,"s-",color="#1565c0",lw=2.5,ms=8,label="Nợ xấu DỰ ĐOÁN của danh mục duyệt")
b.plot(x,nx_that,"o--",color="#ef6c00",lw=2.5,ms=8,label="Nợ xấu THẬT (theo giá trị) – lô kiểm chứng")
b.plot(x[:5],[2,3,4,5,6],":",color="grey",lw=1.5,label="Trần cho phép r")
b.axhline(8.07,color="#c62828",lw=1.5,ls="-."); b.text(5.4,7.65,"Nợ xấu nền toàn bộ đơn: 8,07%",ha="right",fontsize=11,color="#c62828")
b.set_ylim(0,10.5); b.set_xticks(x); b.set_xticklabels(tran,fontsize=13); b.set_xlabel("Trần nợ xấu danh mục (r)",fontsize=13)
b.set_ylabel("%",fontsize=13); b.tick_params(labelsize=12); b.legend(fontsize=11,loc="upper left",bbox_to_anchor=(0,0.88))
b.axvspan(1.5,5.5,color="#e8f5e9",zorder=0); b.axvline(2,color="#2e7d32",ls="--",lw=1.5)
b.annotate("Hàm mục tiêu tự giới hạn ở 3,18%\n(loại đơn có P > phí/LGD)",(2,3.18),xytext=(2.3,1.0),fontsize=11,arrowprops=dict(arrowstyle="->",color="#1565c0"),color="#1565c0")
b.set_title("(b) Trần ≥ 4% không còn ràng buộc; nợ xấu thật ≈ dự đoán",fontsize=14)
fig.suptitle("Hình 4.3 – Độ nhạy của lời giải MILP theo trần nợ xấu (lô 1.000 đơn, quỹ 2 tỷ, LGD 0,6)",fontsize=15,fontweight="bold")
plt.tight_layout(rect=(0,0,1,0.95)); plt.savefig("do_nhay_tran_rui_ro.png",facecolor="white"); plt.savefig("do_nhay_tran_rui_ro.svg",facecolor="white")
