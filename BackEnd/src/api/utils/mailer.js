const nodemailer = require("nodemailer");

// Cấu hình transporter cho Nodemailer
const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
        user: "kien911002@gmail.com", // Email của bạn
        pass: "lyra thtj gwoa pmgy", // Mật khẩu ứng dụng
    },
});

// Hàm gửi email OTP
async function sendEmail(to, otp) {
    const mailOptions = {
        from: "FrontEnd App",
        to: to,
        subject: "Mã OTP của bạn",
        text: `Mã OTP của bạn là: ${otp}. Mã có hiệu lực trong 5 phút.`,
    };

    await transporter.sendMail(mailOptions);
}

module.exports = { sendEmail };
