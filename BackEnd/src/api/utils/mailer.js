const nodemailer = require("nodemailer");
require("dotenv").config();

const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
        user: process.env.EMAIL_NAME,
        pass: process.env.EMAIL_PASS,
    },
});


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