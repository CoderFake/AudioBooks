const express = require("express");
const { sendOTP, verifyOTP } = require("../controllers/otpController");

const router = express.Router();

// Route gửi OTP
router.post("/send", sendOTP);

// Route xác minh OTP
router.post("/verify", verifyOTP);

module.exports = router;
