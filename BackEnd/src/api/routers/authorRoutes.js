const express = require("express");
const {
    addAuthor,
    updateAuthor,
    deleteAuthor,
    getAllAuthors,
    getAuthorById,
} = require("../controllers/authorController");

const router = express.Router();

router.post("/", addAuthor); // Thêm tác giả
router.put("/:id", updateAuthor); // Sửa tác giả
router.delete("/:id", deleteAuthor); // Xóa tác giả
router.get("/", getAllAuthors); // Lấy danh sách tác giả
router.get("/:id", getAuthorById); // Lấy chi tiết tác giả theo ID

module.exports = router;
