const User = require("../models/userModel");
const Chapter = require("../models/chapterModel");
const Book = require("../models/bookModel");
const { formateDate } = require("../utils/fomatdate");

exports.updateUserInfo = async (req, res) => {
    const { userId } = req.params;
    const { dateOfBirth, avatarURL, username } = req.body;

    try {
        const user = await User.findById(userId);
        if (!user) {
            return res.status(404).json({ error: "Người dùng không tồn tại" });
        }
        if (dateOfBirth) {
            const formatDate = formateDate(dateOfBirth);
            user.dateOfBirth = formatDate || user.dateOfBirth;
        }

        user.avatarURL = avatarURL || user.avatarURL;
        user.username = username || user.username;
        await user.save();
        res.status(200).json({
            message: "Cập nhật thông tin thành công",
            user,
        });
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi cập nhật thông tin người dùng",
            details: error.message,
        });
    }
};
exports.toggleSaveBook = async (req, res) => {
    const { userId, bookId } = req.body;

    try {
        // Tìm người dùng
        const user = await User.findById(userId);
        if (!user) {
            return res.status(404).json({ error: "Người dùng không tồn tại" });
        }

        // Kiểm tra nếu sách đã có trong danh sách đã lưu
        const isSaved = user.savedBooks.includes(bookId);

        if (isSaved) {
            // Nếu sách đã có, xóa khỏi danh sách đã lưu
            user.savedBooks = user.savedBooks.filter(
                (id) => !id.equals(bookId)
            );
            await user.save();
            return res.status(200).json({
                message: "Sách đã được xóa khỏi danh sách đã lưu",
                user,
            });
        } else {
            // Nếu sách chưa có, thêm vào danh sách đã lưu
            user.savedBooks.push(bookId);
            await user.save();
            return res.status(200).json({
                message: "Sách đã được lưu thành công",
                user,
            });
        }
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi lưu hoặc xóa sách",
            details: error.message,
        });
    }
};

// Lấy danh sách những quyển sách đã lưu
exports.getSavedBooks = async (req, res) => {
    const { userId } = req.params; // Lấy userId từ params

    try {
        // Tìm người dùng
        const user = await User.findById(userId).populate("savedBooks"); // Populates savedBooks để lấy thông tin sách
        if (!user) {
            return res.status(404).json({ error: "Người dùng không tồn tại" });
        }

        // Trả về danh sách sách đã lưu
        res.status(200).json({
            message: "Danh sách sách đã lưu",
            savedBooks: user.savedBooks, // Trả về danh sách sách
        });
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi lấy danh sách sách đã lưu",
            details: error.message,
        });
    }
};

exports.updateFavoriteGenres = async (req, res) => {
    const { userId } = req.params; // Lấy ID người dùng từ URL
    const { favorite } = req.body; // Nhận danh sách thể loại từ body

    try {
        // Kiểm tra user có tồn tại không
        const user = await User.findById(userId);
        if (!user) {
            return res.status(404).json({ message: "User not found" });
        }

        // Cập nhật mảng favorite
        user.favorite = favorite;
        await user.save();

        res.status(200).json({
            message: "Favorite genres updated successfully",
            user,
        });
    } catch (err) {
        res.status(500).json({
            message: "Error updating favorite genres",
            error: err.message,
        });
    }
};

exports.getUserById = async (req, res) => {
    const { userId } = req.params;

    try {
        const user = await User.findById(userId).populate({
            path: "savedBooks",
            populate: {
                path: "author", // Lấy thông tin tác giả của sách
                model: "Author",
            },
        });
        if (!user) {
            return res.status(404).json({ message: "User not found" });
        }

        res.status(200).json(user);
    } catch (err) {
        res.status(500).json({
            message: "Error fetching user",
            error: err.message,
        });
    }
};

exports.markChapterAsRead = async (req, res) => {
    const { userId, chapterId, bookId } = req.body;

    try {
        // Kiểm tra người dùng có tồn tại không
        const user = await User.findById(userId);
        if (!user) {
            return res.status(404).json({ error: "Người dùng không tồn tại" });
        }

        // Kiểm tra xem sách có tồn tại không
        const book = await Book.findById(bookId);
        if (!book) {
            return res.status(400).json({ message: "Sách không tồn tại" });
        }

        // Kiểm tra xem chương có tồn tại không và có thuộc sách không
        const chapter = await Chapter.findOne({
            _id: chapterId,
            book_id: bookId,
        });
        if (!chapter) {
            return res
                .status(400)
                .json({
                    message: "Chương không thuộc sách này hoặc không tồn tại",
                });
        }

        // Tìm xem sách đã có trong danh sách readChapters chưa
        const existingBook = user.readChapters.find(
            (entry) => entry.bookId.toString() === bookId.toString()
        );

        if (existingBook) {
            // Nếu chương đã được đánh dấu đọc trước đó, không thêm lại
            if (existingBook.chapterIds.includes(chapterId)) {
                return res
                    .status(400)
                    .json({ message: "Chương này đã được đánh dấu là đã đọc" });
            }

            // Thêm chapterId vào danh sách chương đã đọc
            existingBook.chapterIds.push(chapterId);
        } else {
            // Nếu sách chưa có trong readChapters, thêm mới
            user.readChapters.push({ bookId, chapterIds: [chapterId] });
        }

        await user.save();
        res.status(200).json({
            message: "Đánh dấu chương đã đọc thành công",
            user,
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            error: "Lỗi khi đánh dấu chương đã đọc",
            details: error.message,
        });
    }
};

// Lấy danh sách chương đã đọc của một user
exports.getReadChapters = async (req, res) => {
    const { userId } = req.params;

    try {
        const user = await User.findById(userId)
            .populate("readChapters.bookId") // Lấy thông tin sách
            .populate("readChapters.chapterIds"); // Lấy thông tin chương

        if (!user) {
            return res.status(404).json({ error: "Người dùng không tồn tại" });
        }

        res.status(200).json({ readChapters: user.readChapters });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            error: "Lỗi khi lấy danh sách chương đã đọc",
            details: error.message,
        });
    }
};
