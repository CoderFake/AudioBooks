const User = require("../models/userModel");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcrypt");

exports.register = async (req, res) => {
    let { username, accountname, email, password } = req.body;

    try {
        // Kiểm tra đầu vào có thiếu dữ liệu không
        if (!username || !accountname || !email || !password) {
            return res.status(400).json({ message: "All fields are required" });
        }

        // Chuẩn hóa accountname (viết thường để tránh trùng lặp do chữ hoa/chữ thường)
        accountname = accountname.toLowerCase();

        // Kiểm tra nếu email hoặc accountname đã tồn tại (username có thể trùng lặp)
        const existingUser = await User.findOne({
            $or: [{ email }, { accountname }],
        });
        if (existingUser) {
            return res
                .status(400)
                .json({ message: "Email or accountname already exists" });
        }

        // Tạo người dùng mới
        const newUser = new User({
            username,
            accountname,
            email,
            password,
        });
        await newUser.save();

        res.status(201).json({
            message: "User registered successfully",
            user: {
                id: newUser._id,
                username: newUser.username,
                accountname: newUser.accountname,
                email: newUser.email,
                createdAt: newUser.createdAt, // Thêm thời gian tạo
            },
        });
    } catch (err) {
        res.status(500).json({
            message: "Error registering user",
            error: err.message,
        });
    }
};

exports.login = async (req, res) => {
    const { accountname, password } = req.body;

    try {
        // Tìm user theo accountname
        const user = await User.findOne({ accountname })
            .populate("savedBooks")
            .populate("readChapters");

        // Kiểm tra nếu người dùng không tồn tại
        if (!user) return res.status(404).json({ message: "User not found" });

        // Kiểm tra mật khẩu (bạn cần mã hóa mật khẩu khi đăng ký)
        const isMatch = await bcrypt.compare(password, user.password);

        if (!isMatch)
            return res.status(400).json({ message: "Invalid credentials" });

        // Tạo token JWT
        const token = jwt.sign(
            { id: user._id, accountname: user.accountname },
            process.env.JWT_SECRET,
            { expiresIn: process.env.JWT_EXPIRES_IN }
        );

        // Trả về thông tin người dùng và token
        res.json({
            message: "Login successful",
            token,
            user: {
                id: user._id,
                accountname: user.accountname,
                username: user.username,
                email: user.email,
                dateOfBirth: user.dateOfBirth,
                avatarURL: user.avatarURL,
                favorite: user.favorite,
                savedBooks: user.savedBooks, // Danh sách sách đã lưu
                readChapters: user.readChapters, // Các chương đã đọc
            },
        });
    } catch (err) {
        res.status(500).json({
            message: "Error logging in",
            error: err.message,
        });
    }
};
