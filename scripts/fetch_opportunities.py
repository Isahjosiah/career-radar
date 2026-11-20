"""Hourly job: pull feeds, score them against Josiah's profile, merge with curated items."""
import json,re,html,datetime as dt,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parent.parent/"data"
FEEDS=[("Opportunity Desk","https://opportunitydesk.org/category/fellowships-and-scholarships/postdoctoral/feed/","Postdoc"),
("Opportunities for Africans","https://www.opportunitiesforafricans.com/category/fellowships/feed/","Postdoc"),
("FundsforNGOs","https://www2.fundsforngos.org/feed/","Grant")]
JOBS=["computational chemistry","cheminformatics","drug discovery"]
STRONG=["drug discovery","cheminformatics","computational chemistry","medicinal chemistry","computer-aided","qsar","molecular","bioinformatics","machine learning","artificial intelligence","lymphoma","cancer","in silico"]
MID=["chemistry","pharma","health","postdoc","early-career","early career","life science","biotech"]
REGION=["africa","nigeria","developing countr","low- and middle","worldwide","anywhere"]
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"career-radar/1.0"}),timeout=30).read()
def score(t):
    t=t.lower();return 2*sum(k in t for k in STRONG)+sum(k in t for k in MID)+sum(k in t for k in REGION)
def fit(n):return "High" if n>=7 else "Medium" if n>=4 else None
def deadline(t):
    m=re.search(r"[Dd]eadline:?\s*(\d{1,2}(?:st|nd|rd|th)?[ -]\w+,?[ -]\d{4}|\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})",t)
    if not m:return None
    x=re.sub(r"(\d)(st|nd|rd|th)",r"\1",m.group(1)).replace(",","").replace("-"," ")
    for f in("%d %B %Y","%d %b %Y","%B %d %Y","%b %d %Y"):
        try:return dt.datetime.strptime(x,f).strftime("%Y-%m-%d")
        except ValueError:pass
def clean(s):return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()
auto=[]
for src,url,typ in FEEDS:
    try:root=ET.fromstring(get(url))
    except Exception as e:print("feed failed",src,e);continue
    for it in root.iter("item"):
        title=clean(it.findtext("title"));body=clean(it.findtext("description"))
        n=score(title+" "+body);f=fit(n)
        if not f:continue
        auto.append(dict(t=typ,title=title,org=src,d=deadline(title+" "+body),fit=f,why=body[:230]+("…" if len(body)>230 else ""),note="Auto-found on "+src+". Confirm details on the official page.",u=it.findtext("link"),auto=True,_n=n))
for q in JOBS:
    try:j=json.loads(get("https://remotive.com/api/remote-jobs?search="+q.replace(" ","%20")))
    except Exception as e:print("jobs failed",q,e);continue
    for x in j.get("jobs",[]):
        loc=x.get("candidate_required_location","").lower()
        if not any(k in loc for k in("worldwide","anywhere","africa","nigeria")):continue
        n=score(x["title"]+" "+clean(x.get("description",""))[:1500])
        f=fit(n)
        if not f:continue
        auto.append(dict(t="Job",title=x["title"],org=x.get("company_name","")+", remote ("+x.get("candidate_required_location","")+")",d=None,fit=f,why=clean(x.get("description",""))[:230]+"…",note="Auto-found via Remotive. Confirm eligibility.",u=x["url"],auto=True,_n=n))
cur=json.loads((R/"curated.json").read_text("utf8"))
seen={i["u"] for i in cur}
old=json.loads((R/"opportunities.json").read_text("utf8"))["items"] if (R/"opportunities.json").exists() else []
pool={i["u"]:i for i in old if i.get("auto")}
for a in auto:pool[a["u"]]=a
cut=(dt.date.today()-dt.timedelta(days=30)).isoformat()
keep=[i for u,i in pool.items() if u not in seen and not(i.get("d") and i["d"]<cut)]
keep.sort(key=lambda i:-i.get("_n",0))
for i in keep:i.pop("_n",None)
out={"updated":dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"items":cur+keep[:120]}
(R/"opportunities.json").write_text(json.dumps(out,ensure_ascii=False,indent=1),"utf8")
print("curated",len(cur),"auto",len(keep))
