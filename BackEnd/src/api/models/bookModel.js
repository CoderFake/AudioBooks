const mongoose = require("mongoose");

const bookSchema = new mongoose.Schema(
    {
        title: { type: String, required: true },
        description: String,
        author: {
            type: mongoose.Schema.Types.ObjectId,
            ref: "Author",
            required: true,
        },
        genre: { type: [String], default: [] },
        image: String,
        audio_url: String,
        chapters: [{ type: mongoose.Schema.Types.ObjectId, ref: "Chapter" }],
        comments: [{ type: mongoose.Schema.Types.ObjectId, ref: "Comment" }],
        ratings: [{ type: mongoose.Schema.Types.ObjectId, ref: "Rating" }],
    },
    { timestamps: true }
);

module.exports = mongoose.model("Book", bookSchema);
