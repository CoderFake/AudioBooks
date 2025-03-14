const { sendEmail } = require("../utils/mailer");
var jwt = require("jsonwebtoken");
require("dotenv").config();
const OTP = require("../models/otpModel");
// Hàm tạo OTP
function generateOTP() {
    return Math.floor(100000 + Math.random() * 900000); // Tạo OTP 6 chữ số
}

// Gửi OTP
function generateOtpToken(email, otp) {
    const OTP_SECRET = process.env.OTP_SECRET;
    const payload = { email, otp }; // Payload chứa OTP
    const options = { expiresIn: "5m" }; // OTP có hiệu lực trong 5 phút
    const token = jwt.sign(payload, OTP_SECRET, options); // Mã hóa JWT bằng HS256 (HMAC với SHA-256).
    return token;
}

function verifyOtpToken(token) {
    try {
        const OTP_SECRET = process.env.OTP_SECRET;
        const decoded = jwt.verify(token, OTP_SECRET); // Giải mã token
        return decoded; // Trả về OTP nếu token hợp lệ
    } catch (error) {
        throw new Error("Token không hợp lệ hoặc đã hết hạn.");
    }
}

async function sendOTP(req, res) {
    const { email } = req.body;

    try {
        const otp = generateOTP(); // Tạo OTP ngẫu nhiên
        const token = generateOtpToken(email, otp); // Mã hóa OTP vào JWT

        // Gửi OTP qua email
        await sendEmail(email, otp);

        res.status(200).json({
            success: true,
            message: "Mã OTP đã được gửi thành công",
            token: token, // Gửi token OTP cho client để xác minh sau này
        });
    } catch (error) {
        console.error("Lỗi khi gửi OTP:", error);
        res.status(500).send({ error: "Không thể gửi OTP" });
    }
}

async function verifyOTP(req, res) {
    const { token, otp } = req.body; // Nhận token & OTP từ request

    try {
        const decoded = verifyOtpToken(token); // Giải mã JWT
        const storedOtp = decoded.otp; // OTP ban đầu từ JWT
        // Kiểm tra OTP nhập vào có đúng không
        if (storedOtp !== otp) {
            return res.status(400).json({ error: "OTP không hợp lệ." });
        }

        res.status(200).json({ message: "OTP hợp lệ!" });
    } catch (error) {
        return res.status(400).json({ error: error.message });
    }
}

module.exports = { sendOTP, verifyOTP };
