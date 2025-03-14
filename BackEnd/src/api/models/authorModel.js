const mongoose = require("mongoose");

const authorSchema = new mongoose.Schema(
    {
        name: { type: String, required: true },
        birthplace: { type: String, required: true },
        birthdate: { type: Date, required: true },
        biography: { type: String },
        avatarUrl: { type: String },
        books: [{ type: mongoose.Schema.Types.ObjectId, ref: "Book" }], // Danh sách sách của tác giả
    },
    { timestamps: true }
);

const Author = mongoose.model("Author", authorSchema);

module.exports = Author;
