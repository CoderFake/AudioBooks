const mongoose = require("mongoose");

const chapterSchema = new mongoose.Schema(
    {
        book_id: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "Book",
            required: true,
        },
        title: { type: String, required: true },
        content: String,
        audio_url: String,
        index: { type: Number, required: true },
    },
    { timestamps: true }
);

module.exports = mongoose.model("Chapter", chapterSchema);
