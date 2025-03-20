document.currentScript.value=async (root,args)=>{

	function __sync__ () {
		if (document.App.UserProfile && document.App.UserProfile.A) {
			root.setAttribute("UserProfile",document.App.UserProfile.A);
			(async function (form) {
				(new Piers.Widget.Form(form)).set(document.App.UserProfile);
			})(root.querySelector('[WidgetTag="vn"]'));
		} else if (root.hasAttribute("UserProfile"))
			root.removeAttribute("UserProfile");
	}
	__sync__();


	(function(ra){
		if (ra.PiersClickHandler)
			ra.removeEventListener("click",ra.PiersClickHandler);
		ra.addEventListener("click",ra.PiersClickHandler=function(evt){
			let act;
			try{ act=evt.target.getAttribute("act"); }catch(x){ }
			switch(act){
			case "passwd":
				(async function (e) {
					if (e.getAttribute("Fold")==='y') {
						e.querySelector('[vn="A"]').value=document.App.UserProfile.A;
						e.setAttribute("Fold","n");
					} else {
						let newpass,res;
						newpass=e.querySelector('[vn="S"]').value;
						if (newpass!==e.querySelector('[vn="SV"]').value)
							return alert("確認密碼錯誤");
						res = await document.App.request("home/auth",{
							"A":"porshenlai",
							"S":Piers.Session.SHA_b64("porshenlai:"+newpass)
						});
						alert(res.R==="OK" ? "密碼修改成功" : "密碼修改失敗");
						e.setAttribute("Fold","y");
						document.App.updateUserProfile({});
						__sync__();
					}
				})(evt.target.parentNode);
				break;
			case "login":
				(async function (fe) {
					let form = Piers.DOM(fe).reduce(function(r,v){
						r[v.getAttribute("vn")] = v.value;
						if (v.getAttribute("type")==="password") v.value="";
						return r;
					},"[vn]",{}), msg,res;

					form.S = Piers.Session.SHA_b64(form.A+":"+form.S);
					res = await document.App.request("home/auth",{"A":form.A});
					if (res.R === "OK") {
						form.T = res.A.T;
						form.S = Piers.Session.SHA_b64(form.A+":"+form.T+":"+form.S);
						res = await document.App.request("home/auth",form);
						if (res.R === "OK") {
							document.App.updateUserProfile(res.A);
							fe.querySelector('[vn="msg"]').textContent
							msg = "";
						} else
							msg = "登入失敗";
					} else
						msg = "登入錯誤";
					fe.querySelector('[vn="msg"]').textContent=msg;
					__sync__();
				})(Piers.DOM(evt.target).find("form"));
				break;
			case "logout":
				(async function (form) {
					document.App.updateUserProfile({});
					__sync__();
				})(Piers.DOM(evt.target).find("form"));
				break;
			}
		});
	})(root.querySelector(".ActHandler"));
};
