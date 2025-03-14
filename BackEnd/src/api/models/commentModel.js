const mongoose = require("mongoose");

const commentSchema = new mongoose.Schema({
    book_id: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Book",
        required: true,
    },
    user_id: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User",
        required: true,
    },
    comment: String,
    created_at: { type: Date, default: Date.now },
});

module.exports = mongoose.model("Comment", commentSchema);
