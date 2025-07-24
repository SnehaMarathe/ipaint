// ipaint-backend/routes/wish.js
const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

const DATA_FILE = path.join(__dirname, '../data/wishes.json');

router.post('/', (req, res) => {
  const { toName, toAddress, fromName, mobileNumber, message } = req.body;

  if (!toName || !toAddress || !fromName || !mobileNumber || !message) {
    return res.status(400).json({ message: 'All fields are required.' });
  }

  const newWish = {
    id: Date.now().toString(),
    toName, toAddress, fromName, mobileNumber, message,
    createdAt: new Date().toISOString()
  };

  let wishes = [];
  if (fs.existsSync(DATA_FILE)) {
    wishes = JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
  }
  wishes.unshift(newWish);
  fs.writeFileSync(DATA_FILE, JSON.stringify(wishes, null, 2));

  res.json({ message: 'Wish recorded successfully.', wish: newWish });
});

router.get('/', (req, res) => {
  let wishes = [];
  if (fs.existsSync(DATA_FILE)) {
    wishes = JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
  }
  res.json(wishes);
});

module.exports = router;
