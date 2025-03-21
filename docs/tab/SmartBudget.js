document.currentScript.value=async (root,args)=>{
	console.log("Table: ",root,args);

	let Dict={
		"TWD":"臺幣",
		"JPY":"日圓",
		"EUR":"歐元",
		"USD":"美金",
		"C_TWD":"信用卡",
		"CP_TWD":"預購"
	}

	function gw (e,WN="Form"){
		if("string"===typeof(e)) e=root.querySelector(e);
		return e._gw ? e._gw() : new Piers.Widget[WN](e);
	}

	function o2a(o) {
		return Object.keys(o).reduce((r,v)=>r.push({"K":v,"V":o[v]})&&r,[]);
	}

	class YM {
		constructor (d) { // {{{
			if (!d) d = new Date();
			if ("string" === typeof(d)) d=parseInt(d);
			this.Value = ("number" === typeof(d))
				? [Math.floor(d/100),(d%100)-1]
				: [d.getFullYear(),d.getMonth()];
		} // }}}
		dist (dt) { // {{{
			if (!(dt instanceof YM)) dt = new YM(dt);
			return (dt.Value[0] - this.Value[0])*12+dt.Value[1]-this.Value[1];
		} // }}}
		toString () { // {{{
			return this.Value[0]+((v)=>v<10?("0"+v):v)(this.Value[1]+1);
		} // }}}
	}

	class MapDB { // 轉換資料庫
		constructor (url) { // {{{
			this.Ref = new YM(new Date(2000,0,1));
			this._P_ = this.init(url);
		}	// }}}
		async init (url) { // {{{
			this.DB = await document.App.request(url);
			this.DB.USD = [1,1,1,1,1];
			this.Regression = await Piers.import(Piers.Env.PierPath+"Regression.js");
		}	// }}}
		async waitInit () {	// {{{
			return await this._P_;
		}	// }}}
	}
	
	class CxDB extends MapDB {
		constructor (url) {	// {{{
			super(url);
		}	// }}}
		getRate (cn, x) { // {{{
			let db = this.DB;
			if (!(cn in db)) return 1;
			if (!x) return db[cn][0];
			let eq = this.Regression('polynomial', [
				[this.Ref.dist("202502"),db[cn][1]],
				[this.Ref.dist("202505"),db[cn][2]],
				[this.Ref.dist("202508"),db[cn][3]],
				[this.Ref.dist("202511"),db[cn][4]]
			], 4);
			x = this.Ref.dist(x);
			eq = eq.equation;
			return (x*x*x*x)*eq[4] + (x*x*x)*eq[3] + (x*x)*eq[2] + (x)*eq[1] + eq[0] ;
		}	// }}}
		convert (from, to, amount, dt="") { // {{{
			return amount*this.getRate(to,dt)/this.getRate(from,dt);
		}	// }}}
	}

	class LxDB extends MapDB {
		constructor (url) {	// {{{
			super(url);
		}	// }}}
		convert (from, to, amount, type=0) { // {{{
			// 1: rent, 3: grocery, 4: restaurant
			return amount*this.DB[to][type]/this.DB[from][type];
		}	// }}}
	}

	// let currency = new CvDB("tab/SmartBudget/Currency.json");
	// let living = new CvDB("tab/SmartBudget/Life.json");
	// await currency.convert("EUR","TWD",10000);
	// await living.convert("Taipei, Taiwan", "New York, NY, United States", 300, 4);

	/*let rst = await document.App.request("home/file",{"F":"w","N":"test2","D":{"A":1,"B":2,"C":3}});
	console.log("Write Test Result is ",rst);
	rst = await document.App.request("home/file",{"F":"r","N":"test2"});
	console.log("Data is ",rst.R,rst.D);
	*/

	class Input extends Form {
		constructor (E) {	// {{{
			super(E);
			this.XDB = new CxDB("tab/SmartBudget/Currency.json");
			this.LDB = new LxDB("tab/SmartBudget/Life.json");
			this.Hints = new Piers.Widget.List(this.E.querySelector('[WidgetTag="PA"]'));
			if (E.CHANGE_BIND)
				E.removeEventListener("change", E.CHANGE_BIND);
			E.addEventListener("change", E.CHANGE_BIND=(evt)=>{
				this.updateHints();
			});
			if (E.CLICK_BIND)
				E.removeEventListener("click", E.CLICK_BIND);
			E.addEventListener("click", E.CLICK_BIND=function(evt){
				try {
					let btn=Piers.DOM(evt.target).find('[func]');
					if (!btn) return;
					switch(btn.getAttribute("func")){
					case "Add":
						(function (doc) {
							doc.O = [doc.O].reduce((r,v)=>{
								r[v.T] = parseFloat(v.A);
								return r;
							},{});
							if (null===doc.I) delete doc.I;
							B.addRecord(JSON.parse(JSON.stringify(doc)));
						})(gw(e).get());
						break;
					case "Clear":
						(function (ie) {
							if (!ie) return;
							ie.removeAttribute("__idx__");
						})(Piers.DOM(btn).find('[__idx__]'));
						break;
					case "Remove":
						(function (ie) {
							if (!ie) return;
							if (window.confirm("Remove item ? ")) {
								ie.removeAttribute("__idx__");
								B.removeRecord(ie);
							}
						})(Piers.DOM(btn).find('[__idx__]'));
						break;
					};
				} catch(x) {
				}
			});
			(async (e)=>{ // O.T:Value
				while (e.firstChild) e.removeChild(e.firstChild);
				await this.XDB.waitInit();
				for (let k in this.XDB.DB)
					if(k in Dict)
						Piers.DOM({ "T":"option", "A":{"value":k}, "C":[Dict[k]||k] }).join(e);
			})(this.E.querySelector('[IPT="O.T:Value"]'));
			(async (e)=>{ // #LivingCities
				while (e.firstChild) e.removeChild(e.firstChild);
				await this.LDB.waitInit();
				for (let k in this.LDB.DB)
					Piers.DOM({ "T":"option", "A":{"value":k}, "C":[k] }).join(e);
			})(this.E.querySelector('#LivingCities'));
			(async (e)=>{
				if (e.CHANGE_BIND)
					e.removeEventListener("change", E.CHANGE_BIND);
				e.addEventListener("change", E.CHANGE_BIND=(evt) => {
					let w = gw(e,"Form"), doc=w.get();
					doc.T = Math.floor(1000*this.LDB.convert("Taipei, Taiwan",doc.D,doc.F,4))/1000;
					w.set(doc);
					evt.stopPropagation();
					evt.preventDefault();
				});
			})(this.E.querySelector('[WidgetTag="LCH"]'));

			this.updateHints();
		}	// }}}
		updateHints () {	// {{{
			let doc = this.get();
			console.log("INPUT is ",doc);

			let Payments={"TWD":["消費日換匯"],"C_TWD":["消費隔月換匯"],"CP_TWD":["隔月換匯"]};
			(async (e)=>{ // M:Value
				let p={};
				p[doc.O.T||"TWD"]=["今日換匯"];
				p=Object.assign(p,Payments);
				while (e.firstChild) e.removeChild(e.firstChild);
				for (let k in p)
					Piers.DOM({ "T":"option", "A":{"value":k}, "C":[Dict[k]||k] }).join(e);
				
				if( doc.O.T && doc.O.A ) {
					await this.XDB.waitInit();
					this.Hints.set(Piers.OBJ(p).reduce((r,v,k)=>{
						r.push({
							"N":Dict[k]||k,
							"V":Math.floor(this.XDB.convert(doc.O.T,"TWD",doc.O.A)*1000)/1000,
							"M":p[k][0]
						});
						return r;
					},[]));
				}
				e.value=doc.M;
			})(this.E.querySelector('[IPT="M:Value"]'));
		}	// }}}
	}

	class Book {
		constructor () {
			this.IPT = new Input(root.querySelector('[WidgetTag="IPT"]'));
			this.xrate={
				"TWD":1,
				"JPY":0.25,
				"EUR":34,
				"USD":33
			};
			this.budgets={
				"TWD":100000,
				"JPY":100000,
				"EUR":10000,
				"USD":10000,
				"C_TWD":200000,
				"CP_TWD":200000,
				"BW":1000000
			};
			this.doc={
				"CN":{"R":"TWD"},
				"L":[
					{"N":"One Dollar","O":{"EUR":1}},
					{"N":"Two Dollar","O":{"USD":2}},
					{"N":"Three Dollar","O":{"USD":3}},
					{"N":"Five Dollar","O":{"JPY":5}}
				],
				"TT":{}
			};
		}
		mdAdd (ov,nv) {
			for(let t in nv){
				if(t in ov) ov[t] = parseFloat(ov[t]) + parseFloat(nv[t]);
				else ov[t] = parseFloat(nv[t]);
			}
		}
		mdConv (ov, tp) {
			let r=0;
			for(let t in ov)
				r += ov[t]*this.xrate[t]
			return r;
		}
		recalc () {
			let tto={}, self=this;
			this.doc.L.forEach(function(row){
				row.R = self.mdConv(row.O);
				self.mdAdd(tto,row.O);
			});
			this.doc.TT.O=tto;
			this.doc.TT.R=this.mdConv(tto);
		}
		addRecord (r) {
			if (undefined!==r.I){
				let idx=r.I;
				delete r.I;
				this.doc.L[idx]=r;
			}else this.doc.L.push(r);
			this.redraw();
		}
		removeRecord (idx) {
			this.doc.L.splice(idx,1);
			this.redraw();
		}
		redraw () {
			this.recalc();
			function oc(o){
				let no=[],t;
				for(t in o) no.push({"T":t,"A":o[t]});
				return no;
			}
			gw('[UIE="List"] [WidgetTag="cn"]').set(this.doc.CN);
			
			gw('[UIE="List"] [WidgetTag="item"]',"List").set(this.doc.L.reduce(function(r,v){
				r.push({"N":v.N, "O":oc(v.O), "R":v.R});
				return r;
			},[]));
			gw('[UIE="List"] [WidgetTag="tt"]').set({"O":oc(this.doc.TT.O),"R":this.doc.TT.R});
		}
	}

	let B=new Book();
	B.redraw();

	(function(e){
		if(e.CLICK_BIND)
			e.removeEventListener("click",e.CLICK_BIND);
		e.addEventListener("click",e.CLICK_BIND=function(evt){
			try {
				let btn=Piers.DOM(evt.target).find('[func]');
				if (!btn) return;
				switch(btn.getAttribute("func")){
				case "Select":
					(function (e) {
						// TODO the input UI only support one record with one dollar type now.
						let doc = gw(e).get();
						gw('[WidgetTag="IPT"]').set({
							"N":doc.N,
							"O":doc.O[0],
							"I":e.getAttribute("__idx__")
						});
					})(btn);
					break;
				};
			} catch(x) {
			}
		});
	})(root.querySelector('[UIE="List"]'));
};
