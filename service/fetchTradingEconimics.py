from pandas import read_html
from json import dump
from time import strftime

headers = {"User-Agent": "Mozilla/5.0"}
df = read_html("https://tradingeconomics.com/forecast/currency/",storage_options=headers)

rs = {}                                                                                                  
for c in range(1,5) :
	tb = df[c][df[c].columns[1:3].tolist()+df[c].columns[4:8].tolist()]
	for d in tb.values :
		if len(d) < 6 : continue                                                                             
		(fn,tn,dd) = (d[0][0:3],d[0][3:6],d[1:].tolist())
		if fn != "USD" : (fn,tn,dd) = (tn,fn,[ int(1000/i)/1000 for i in dd])
		rs[tn] = dd

with open(strftime("%Y%m%d")+".json","w",encoding="utf8") as fo :
	dump(rs,fo,ensure_ascii=False)
