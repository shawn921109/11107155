from pandas import read_html
from json import dump
from time import strftime

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://www.numbeo.com/cost-of-living/rankings_current.jsp"
# Cost of Living, Rent, Cost of Living+Rent, Groceries, Restaurant, Local Purchasing Power
df = read_html(url, storage_options=headers)

rs = {}                                                                                                  
tb = df[1][df[1].columns[1:].tolist()]
for d in tb.values :
	if len(d) < 1 : continue                                                                             
	rs[d[0]] = d[1:].tolist()

with open("Restaurant_"+strftime("%Y%m%d")+".json","w",encoding="utf8") as fo :
	dump(rs,fo,ensure_ascii=False)
