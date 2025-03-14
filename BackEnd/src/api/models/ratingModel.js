const mongoose = require("mongoose");

const ratingSchema = new mongoose.Schema({
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
    rating: { type: Number, min: 1, max: 5, required: true },
    created_at: { type: Date, default: Date.now },
});

module.exports = mongoose.model("Rating", ratingSchema);
