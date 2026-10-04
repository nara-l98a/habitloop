from __future__ import annotations
import argparse,json,os,sys,tempfile
from datetime import date,timedelta
from pathlib import Path

def pd(s):
    try:
        parsed=date.fromisoformat(s)
        if parsed.isoformat()!=s:raise ValueError
        return parsed
    except ValueError as e:raise ValueError(f"无效日期：{s}，请使用 YYYY-MM-DD") from e
def fs(d):return d.isoformat()
def path(v):return Path(v or os.environ.get("HABITLOOP_DATA","~/.habitloop.json")).expanduser()
def load(p):
    if not p.exists():return {"version":1,"next_id":1,"habits":[]}
    try:
        x=json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(x,dict) or not isinstance(x.get("habits"),list):raise ValueError
        return x
    except (OSError,json.JSONDecodeError,ValueError) as e:raise RuntimeError(f"无法读取数据文件：{p}") from e
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True); fd,t=tempfile.mkstemp(prefix="."+p.name+".",dir=p.parent,text=True)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
        os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
def habit(db,i):
    try:i=int(i)
    except ValueError as e:raise ValueError("习惯 ID 必须是整数") from e
    for h in db["habits"]:
        if h["id"]==i:return h
    raise ValueError(f"找不到习惯：{i}")
def days(h):return {pd(x) for x in h.get("checkins",[])}
def wks(a,b):
    a=a-timedelta(days=a.weekday());b=b-timedelta(days=b.weekday())
    while a<=b:yield a;a+=timedelta(days=7)
def streak(h,r):
    ds=days(h);n=0
    if h["cadence"]=="daily":
        while r in ds:n+=1;r-=timedelta(days=1)
    else:
        while True:
            c=sum(m<=d<=m+timedelta(days=6) for d in ds if (m:=r-timedelta(days=r.weekday())))
            if c<h["target"]:break
            n+=1;r-=timedelta(days=7)
    return n
def add(a,p,db):
    if not a.name.strip():raise ValueError("习惯名称不能为空")
    if a.cadence=="daily" and a.target!=1:raise ValueError("daily 习惯目标必须为 1")
    if a.cadence=="weekly" and not 1<=a.target<=7:raise ValueError("weekly 目标必须为 1 至 7")
    if any(h["name"].casefold()==a.name.strip().casefold() for h in db["habits"]):raise ValueError("已存在同名习惯")
    h={"id":db.get("next_id",1),"name":a.name.strip(),"cadence":a.cadence,"target":a.target,"created":fs(date.today()),"checkins":[]};db["next_id"]=h["id"]+1;db["habits"].append(h);save(p,db);print(f"已创建 #{h['id']} {h['name']}（{h['cadence']}，目标 {h['target']}）")
def check(a,p,db,remove=False):
    h=habit(db,a.id);d=pd(a.date or fs(date.today()))
    if d>date.today():raise ValueError("不能为未来日期打卡")
    ds=days(h)
    if remove:
        if d not in ds:raise ValueError("该日期没有打卡，无需取消")
        h["checkins"].remove(fs(d));save(p,db);print(f"已取消 {h['name']} 在 {fs(d)} 的打卡");return
    if d in ds:raise ValueError(f"重复打卡：{h['name']} 已在 {fs(d)} 打卡")
    h["checkins"].append(fs(d));h["checkins"].sort();save(p,db);print(f"已打卡：{h['name']} / {fs(d)}")
def report(a,db):
    h=habit(db,a.id);end=pd(a.end or fs(date.today()));start=pd(a.start) if a.start else end-timedelta(days=29)
    if start>end:raise ValueError("开始日期不能晚于结束日期")
    ds=days(h);count=sum(start<=d<=end for d in ds); ws=list(wks(start,end))
    rate=count/((end-start).days+1)*100 if h["cadence"]=="daily" else (sum(sum(w<=d<=w+timedelta(days=6) for d in ds)>=h["target"] for w in ws)/len(ws)*100 if ws else 0.0)
    print(f"{h['name']} 报告 {fs(start)} 至 {fs(end)}\n打卡次数：{count}；周期完成率：{rate:.1f}%")
def parser():
    p=argparse.ArgumentParser(prog="habitloop",description="本地习惯追踪工具");p.add_argument("--data","--db",dest="data");s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("add");a.add_argument("name");a.add_argument("--cadence",choices=["daily","weekly"],default="daily");a.add_argument("--target",type=int,default=1)
    s.add_parser("list")
    for n in ("checkin","uncheck"):
        q=s.add_parser(n);q.add_argument("id");q.add_argument("--date")
    q=s.add_parser("status");q.add_argument("--date")
    q=s.add_parser("calendar");q.add_argument("id");q.add_argument("--month",default=date.today().strftime("%Y-%m"))
    q=s.add_parser("report");q.add_argument("id");q.add_argument("--start");q.add_argument("--end")
    return p
def main(argv=None):
    try:
        a=parser().parse_args(argv);p=path(a.data);db=load(p)
        if a.cmd=="add":add(a,p,db)
        elif a.cmd=="list":
            print("暂无习惯。使用 add 创建。") if not db["habits"] else [print(f"#{h['id']} {h['name']} | {h['cadence']} | 目标 {h['target']} | 打卡 {len(h.get('checkins',[]))} 次") for h in db["habits"]]
        elif a.cmd in ("checkin","uncheck"):check(a,p,db,a.cmd=="uncheck")
        elif a.cmd=="status":
            r=pd(a.date or fs(date.today()));[print(f"#{h['id']} {h['name']} | 连续 {streak(h,r)}{'天' if h['cadence']=='daily' else '周'} | 总打卡 {len(days(h))} 次") for h in db["habits"]]
        elif a.cmd=="calendar":
            h=habit(db,a.id);start=pd(a.month+"-01");end=(start.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1);print(f"{h['name']} {a.month} 日历（■=已完成）");print("一 二 三 四 五 六 日");print("   "*start.weekday(),end="");[print(("■" if (d:=start+timedelta(days=i)) in days(h) else f"{d.day:02d}")+("\n" if d.weekday()==6 else " "),end="") for i in range(end.day)];print()
        else:report(a,db)
    except (ValueError,RuntimeError,OSError) as e:print(f"错误：{e}",file=sys.stderr);return 2
    return 0
if __name__=="__main__":sys.exit(main())
