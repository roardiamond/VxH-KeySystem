# VxH Key System

Custom Key System for VoidxHub / Sensitivity Boost.

**Features:**
- Admin Panel se key generate karo
- Custom expiry date & time
- Key revoke / delete
- Simple REST API for validation
- No monetization links / ads

---

## Quick Start

### 1. Deploy Backend (Recommended: Render free)

1. Is repo ko [Render.com](https://render.com) pe New Web Service se connect karo
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python app.py`
4. Environment Variables add karo:
   - `ADMIN_PASSWORD` = apna strong password (jaise `VxH@2026Strong`)
   - `SECRET_KEY` = koi random string (jaise `supersecretkey123456789`)

Deploy hone ke baad URL milega (example: `https://vxh-keysystem.onrender.com`)

### 2. Admin Panel

- Jaao: `https://your-url.onrender.com/admin`
- Password daalo jo `ADMIN_PASSWORD` mein set kiya
- Wahan se keys generate karo (custom date/time expiry ke saath)

### 3. Integrate in your Python script

`sensitivityboost.py` mein key check add karne ke liye `client_example.py` dekho.

---

## API

**Validate Key**
```
POST /api/validate
Content-Type: application/json

{
  "key": "VxH-ABCD-EFGH-IJKL"
}
```

**Response (valid):**
```json
{
  "valid": true,
  "expires_at": "2026-12-31 23:59:59",
  "message": "Key is valid"
}
```

**Response (invalid/expired):**
```json
{
  "valid": false,
  "message": "Key expired or not found"
}
```

---

Made for VoidxHub
