import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getFirestore, collection, addDoc } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyC4Bu2kuNR1F_YzaS1ZujUOHOytuye2_F8",
  authDomain: "ipaint-7b2a5.firebaseapp.com",
  projectId: "ipaint-7b2a5",
  storageBucket: "ipaint-7b2a5.appspot.com",
  messagingSenderId: "470124187831",
  appId: "1:470124187831:web:831554ab7218ac62dbbd32",
  measurementId: "G-NE05L2CS5Y"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

new QRCode(document.getElementById("qrcode"), {
  text: "upi://pay?pa=9822571038@upi&am=25&cu=INR",
  width: 180,
  height: 180
});

document.getElementById('wishForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formMessage = document.getElementById('formMessage');

  const wishData = {
    toName: document.getElementById('toName').value.trim(),
    toAddress: document.getElementById('toAddress').value.trim(),
    fromName: document.getElementById('fromName').value.trim(),
    mobileNumber: document.getElementById('mobileNumber').value.trim(),
    message: document.getElementById('message').value.trim(),
    timestamp: new Date()
  };

  if (!/^\d{10}$/.test(wishData.mobileNumber)) {
    formMessage.textContent = "⚠️ Please enter a valid 10-digit mobile number.";
    formMessage.className = "message-box error";
    formMessage.style.display = "block";
    return;
  }

  try {
    await addDoc(collection(db, 'wishes'), wishData);
    formMessage.textContent = "✅ Your wish has been sent successfully!";
    formMessage.className = "message-box success";
    formMessage.style.display = "block";
    document.getElementById('wishForm').reset();
  } catch (error) {
    console.error("Firestore Error:", error);
    formMessage.textContent = "❌ Failed to send wish. Please try again.";
    formMessage.className = "message-box error";
    formMessage.style.display = "block";
  }

  setTimeout(() => {
    formMessage.style.display = "none";
  }, 4000);
});
