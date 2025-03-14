const nodemailer = require("nodemailer");
require("dotenv").config();

const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com",
    port: 587,
    auth: {
        user: process.env.EMAIL_NAME,
        pass: process.env.EMAIL_PASS,
    },
});
module.exports = transporter;
