const express = require("express");
const { updateFavoriteGenres } = require("../controllers/userController");
const {
    getUserById,
    markChapterAsRead,
    getReadChapters,
    updateUserInfo,
    toggleSaveBook,
    getSavedBooks,
} = require("../controllers/userController");
const router = express.Router();

router.put("/:userId/favorite", updateFavoriteGenres);
router.get("/:userId", getUserById);

//Thêm chương đã đọc vào danh sách
router.post("/markChapter", markChapterAsRead);

// Lấy danh sách chương đã đọc của người dùng
router.get("/:userId/readChapters", getReadChapters);

// Cập nhật thông tin người dùng
router.put("/:userId", updateUserInfo);

// Thêm hoặc xóa sách khỏi danh sách đã lưu
router.post("/:userId/saveBooks", toggleSaveBook);
// Lấy danh sách sách đã lưu của người dùng
router.get("/:userId/saveBooks", getSavedBooks);

module.exports = router;
