import React, { useState } from "react";
import { getFirestore, collection, addDoc } from "firebase/firestore";
import { initializeApp } from "firebase/app";

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_APP_ID
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

const Card = ({ children }) => (
  <div className="bg-white rounded-lg shadow-md border border-gray-200">{children}</div>
);

const CardContent = ({ children, className }) => (
  <div className={className}>{children}</div>
);

export default function PostcardAppreciationPage() {
  const [formData, setFormData] = useState({
    toName: "",
    toAddress: "",
    fromName: "",
    fromMobile: "",
    message: "",
  });

  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await addDoc(collection(db, "postcardSubmissions"), formData);
      setSubmitted(true);
    } catch (error) {
      console.error("Error adding document: ", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-100 via-pink-100 to-blue-100 p-6">
      <section className="text-center py-16">
        <h1 className="text-4xl font-bold text-pink-600 mb-4">
          Swap WhatsApp Wishes for Real-World Joy!
        </h1>
        <p className="text-lg max-w-2xl mx-auto text-gray-700">
          Send imagination-inspired postcards to children – surprise, motivate, and make their day unforgettable.
        </p>
      </section>
      <section className="max-w-3xl mx-auto bg-white rounded-2xl shadow-xl p-8">
        <h2 className="text-2xl font-bold mb-6 text-center text-blue-600">
          Write Your Message – We’ll Imagine & Post It Today!
        </h2>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <input name="toName" placeholder="To: Full Name" value={formData.toName} onChange={handleChange} required className="w-full border border-gray-300 rounded px-3 py-2" />
          <textarea name="toAddress" placeholder="To: Full Address" rows={3} value={formData.toAddress} onChange={handleChange} required className="w-full border border-gray-300 rounded px-3 py-2" />
          <input name="fromName" placeholder="From: Your Name" value={formData.fromName} onChange={handleChange} required className="w-full border border-gray-300 rounded px-3 py-2" />
          <input name="fromMobile" placeholder="From: Mobile Number" type="tel" pattern="[0-9]{10}" value={formData.fromMobile} onChange={handleChange} required className="w-full border border-gray-300 rounded px-3 py-2" />
          <textarea name="message" placeholder="Your Motivational Message" rows={5} maxLength={500} value={formData.message} onChange={handleChange} required className="w-full border border-gray-300 rounded px-3 py-2" />
          <div className="mt-6 text-center">
            <h3 className="text-lg font-semibold mb-2 text-green-600">Scan & Pay ₹25</h3>
            <img src="https://ipaint.in/qr-code-9822571038.png" alt="Pay QR Code" width={200} height={200} className="mx-auto rounded-lg" onError={(e) => { e.currentTarget.src = "https://via.placeholder.com/200?text=QR+Code+Not+Found"; }} />
            <p className="mt-2 text-sm text-gray-600">UPI ID: 9822571038@upi</p>
          </div>
          <div className="text-center mt-8">
            <button type="submit" className="bg-green-500 hover:bg-green-600 text-white text-lg px-6 py-3 rounded-2xl">Imagine & Post My Wish</button>
          </div>
        </form>
        {submitted && <p className="text-center mt-4 text-green-700 font-medium">🎉 Your postcard has been submitted! We’ll imagine and post it today. A confirmation will be sent to your mobile.</p>}
      </section>
    </div>
  );
}