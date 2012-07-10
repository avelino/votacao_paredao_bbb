function LondonFuncs(){
    this.context_vars = {};
}
var london = new LondonFuncs();

function require(src){
    alert(src);
    var script = document.createElement('script');
    script.src = src;
}

