const express = require("express");
const bodyParser = require("body-parser");
const dotenv = require("dotenv");
const connectDB = require("./config/db");

dotenv.config();

const app = express();
app.use(bodyParser.json());

connectDB();

// Import routes
const authRoutes = require("./api/routers/authRoutes");
const bookRoutes = require("./api/routers/bookRoutes");
const userRoutes = require("./api/routers/userRoutes");
const otpRoutes = require("./api/routers/otpRoutes");
const authorRoutes = require("./api/routers/authorRoutes");

app.use("/api/authors", authorRoutes);
app.use("/api/auth", authRoutes);
app.use("/api/books", bookRoutes);
app.use("/api/users", userRoutes);
app.use("/api/otp", otpRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
