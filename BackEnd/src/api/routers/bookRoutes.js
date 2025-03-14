const express = require("express");
const router = express.Router();
const bookController = require("../controllers/bookController");

//  Routes CRUD cho Sách
router.get("/", bookController.getAllBooks);
router.post("/", bookController.createBook);
router.get("/:id", bookController.getBookById);
router.delete("/:id", bookController.deleteBook);

//  Routes quản lý Chapter
router.post("/chapters", bookController.addChapter);
router.get("/:book_id/chapters", bookController.getBookChapters);
router.delete("/chapters/:id", bookController.deleteChapter);

//  Routes quản lý Comment
router.post("/comments", bookController.addComment);
router.get("/:book_id/comments", bookController.getBookComments);
router.delete("/comments/:id", bookController.deleteComment);

//  Routes quản lý Rating
router.post("/ratings", bookController.addRating);
router.get("/:book_id/ratings", bookController.getBookRatings);
router.delete("/ratings/:id", bookController.deleteRating);

module.exports = router;
