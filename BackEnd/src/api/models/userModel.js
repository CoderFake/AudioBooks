const mongoose = require("mongoose");
const bcrypt = require("bcrypt");

const userSchema = new mongoose.Schema(
    {
        accountname: { type: String, required: true, unique: true },
        username: { type: String, required: true },
        email: { type: String, required: true, unique: true },
        password: { type: String, required: true },
        favorite: { type: [String], default: [] },
        dateOfBirth: { type: Date },
        avatarURL: { type: String },
        savedBooks: [{ type: mongoose.Schema.Types.ObjectId, ref: "Book" }],
        readChapters: [
            {
                bookId: {
                    type: mongoose.Schema.Types.ObjectId,
                    ref: "Book",
                    required: true,
                },
                chapterIds: [
                    {
                        type: mongoose.Schema.Types.ObjectId,
                        ref: "Chapter",
                        required: true,
                    },
                ],
            },
        ],
    },
    { timestamps: true }
);
// Mã hóa mật khẩu trước khi lưu
userSchema.pre("save", async function (next) {
    if (this.isModified("password")) {
        this.password = await bcrypt.hash(this.password, 10);
    }
    next();
});

module.exports = mongoose.model("User", userSchema);
