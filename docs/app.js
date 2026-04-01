const API="https://your-backend-url.onrender.com";
let freeUsed=false;
async function generate(){
 const res=await fetch(API+"/generate",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({dob:dob.value,time:time.value,place:place.value})});
 const d=await res.json();result.innerText=d.reading;}
async function ask(){
 if(freeUsed){alert("Pay ₹1");return;}
 freeUsed=true;
 const res=await fetch(API+"/ask",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({question:question.value})});
 const d=await res.json();result.innerText=d.answer;}