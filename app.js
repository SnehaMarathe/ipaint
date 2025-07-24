// ipaint-backend/app.js
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const wishRoute = require('./routes/wish');

const app = express();

app.use(cors({
  origin: process.env.CLIENT_ORIGIN || '*'
}));
app.use(express.json());

app.use('/api/wishes', wishRoute);

app.get('/', (req, res) => {
  res.send('ipaint Backend Running');
});

module.exports = app;
