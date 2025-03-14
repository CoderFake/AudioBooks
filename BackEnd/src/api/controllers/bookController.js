const Book = require("../models/bookModel");
const Chapter = require("../models/chapterModel");
const Comment = require("../models/commentModel");
const Rating = require("../models/ratingModel");
const Author = require("../models/authorModel");
// Lấy danh sách tất cả sách
exports.getAllBooks = async (req, res) => {
    try {
        const books = await Book.find().populate(
            "chapters comments ratings author"
        );
        res.json(books);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Tạo một cuốn sách mới
exports.createBook = async (req, res) => {
    try {
        const { author: authorId, ...bookData } = req.body;

        // Kiểm tra tác giả có tồn tại không
        const author = await Author.findById(authorId);
        if (!author) {
            return res.status(404).json({ message: "Author not found" });
        }

        // Tạo sách mới
        const newBook = new Book({ ...bookData, author: authorId });
        await newBook.save();

        // Cập nhật danh sách sách của tác giả
        author.books.push(newBook._id);
        await author.save();

        res.status(201).json(newBook);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
};

// Lấy chi tiết một cuốn sách theo ID
exports.getBookById = async (req, res) => {
    try {
        const book = await Book.findById(req.params.id).populate(
            "chapters comments ratings author"
        );
        if (!book) return res.status(404).json({ message: "Book not found" });
        res.json(book);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Xóa một cuốn sách
exports.deleteBook = async (req, res) => {
    try {
        const book = await Book.findById(req.params.id);
        if (!book) {
            return res.status(404).json({ message: "Book not found" });
        }

        // Xóa bookId khỏi danh sách books của tác giả
        await Author.findByIdAndUpdate(book.author, {
            $pull: { books: book._id },
        });

        // Xóa sách
        await Book.findByIdAndDelete(req.params.id);

        res.json({ message: "Book deleted successfully" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

exports.addChapter = async (req, res) => {
    try {
        const { book_id, title, content, audio_url } = req.body;

        // Kiểm tra sách có tồn tại không
        const book = await Book.findById(book_id);
        if (!book) return res.status(404).json({ message: "Book not found" });

        // Tìm chương có index lớn nhất trong sách
        const lastChapter = await Chapter.findOne({ book_id })
            .sort({ index: -1 }) // Sắp xếp giảm dần theo index
            .select("index");

        // Nếu lastChapter không tồn tại hoặc index bị undefined, đặt index = 1
        const newIndex =
            lastChapter && !isNaN(lastChapter.index)
                ? lastChapter.index + 1
                : 1;

        // Tạo chương mới với index hợp lệ
        const newChapter = new Chapter({
            book_id,
            title,
            content,
            audio_url,
            index: newIndex,
        });
        await newChapter.save();

        // Thêm chương vào danh sách chapters của sách
        book.chapters.push(newChapter._id);
        await book.save();

        res.status(201).json(newChapter);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Thêm comment vào sách
exports.addComment = async (req, res) => {
    try {
        const { book_id, user_id, comment } = req.body;
        const book = await Book.findById(book_id);
        if (!book) return res.status(404).json({ message: "Book not found" });

        const newComment = new Comment({ book_id, user_id, comment });
        await newComment.save();

        book.comments.push(newComment._id);
        await book.save();

        res.status(201).json(newComment);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Thêm rating vào sách
exports.addRating = async (req, res) => {
    try {
        const { book_id, user_id, rating } = req.body;
        if (rating < 1 || rating > 5)
            return res
                .status(400)
                .json({ message: "Rating must be between 1 and 5" });

        const book = await Book.findById(book_id);
        if (!book) return res.status(404).json({ message: "Book not found" });

        //kiểm tra xem user đã rating chưa
        const existingRating = await Rating.findOne({ book_id, user_id });
        if (existingRating) {
            return res
                .status(400)
                .json({ message: "User has already rated this book" });
        }

        const newRating = new Rating({ book_id, user_id, rating });
        await newRating.save();

        book.ratings.push(newRating._id);
        await book.save();

        res.status(201).json(newRating);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Lấy tất cả các chương của sách
exports.getBookChapters = async (req, res) => {
    try {
        const { book_id } = req.params;
        const chapters = await Chapter.find({ book_id });
        res.json(chapters);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Lấy tất cả comment của sách
exports.getBookComments = async (req, res) => {
    try {
        const { book_id } = req.params;
        const comments = await Comment.find({ book_id });
        res.json(comments);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Lấy tất cả rating của sách
exports.getBookRatings = async (req, res) => {
    try {
        const { book_id } = req.params;
        const ratings = await Rating.find({ book_id });
        res.json(ratings);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Xóa một chương
exports.deleteChapter = async (req, res) => {
    try {
        const { id } = req.params;
        await Chapter.findByIdAndDelete(id);
        res.json({ message: "Chapter deleted successfully" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Xóa một comment
exports.deleteComment = async (req, res) => {
    try {
        const { id } = req.params;
        await Comment.findByIdAndDelete(id);
        res.json({ message: "Comment deleted successfully" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

//  Xóa một rating
exports.deleteRating = async (req, res) => {
    try {
        const { id } = req.params;
        await Rating.findByIdAndDelete(id);
        res.json({ message: "Rating deleted successfully" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};
