document.currentScript.value=async (root,args)=>{
	console.log("Script running...");
	root.querySelector('button[UIE="Start"]').addEventListener('click',function(event){
		document.body.querySelector('[func="SmartBudget"]').click();

	});
};
