const jwt = require('jsonwebtoken');
const SECRET = "MAKENOLOGY_SECRET";
const express = require('express');
const router = express.Router();
const db = require('../db');

// REGISTER
 router.post('/register', async (req, res) => {
  const { name, email, password } = req.body;

  if (!name || !email || !password) {
    return res.status(400).json({ error: "Missing fields" });
  }

  try {
    const hashedPassword = await bcrypt.hash(password, 10);

    // 1. CREATE BUSINESS
    db.run(
      `INSERT INTO businesses (name) VALUES (?)`,
      [name],
      function (err) {
        if (err) return res.status(500).json({ error: err.message });

        const businessId = this.lastID;

        // 2. CREATE USER
        db.run(
          `INSERT INTO users (email, password, business_id)
           VALUES (?, ?, ?)`,
          [email, hashedPassword, businessId],
          function (err) {
            if (err) return res.status(500).json({ error: err.message });

            // 3. CREATE TRIAL
            db.run(
              `INSERT INTO subscriptions (business_id, status, end_date)
               VALUES (?, 'active', datetime('now', '+30 days'))`,
              [businessId],
              function (err) {
                if (err) return res.status(500).json({ error: err.message });

                res.json({ message: "Registered with 30 days trial" });
              }
            );
          }
        );
      }
    );

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
    

// LOGIN
router.post('/login', (req, res) => {
  const { email, password } = req.body;

  db.get(
    `SELECT * FROM users WHERE email = ? AND password = ?`,
    [email, password],
    (err, user) => {
      if (err) return res.status(500).json({ error: err.message });

      if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      // 🔐 CREATE TOKEN
      const token = jwt.sign(
        {
          user_id: user.id,
          business_id: user.business_id
        },
        SECRET,
        { expiresIn: '7d' }
      );

      res.json({
        message: 'Login success',
        token
      });
    }
  );
});