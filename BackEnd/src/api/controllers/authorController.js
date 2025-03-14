const Author = require("../models/authorModel");
const { parse } = require("date-fns");
const moment = require("moment");
// Thêm tác giả
const addAuthor = async (req, res) => {
    try {
        const { name, birthplace, birthdate, biography, avatarUrl } = req.body;
        const dateParts = birthdate.split("/");
        const formattedDate = new Date(
            Date.UTC(dateParts[2], dateParts[1] - 1, dateParts[0])
        );
        const newAuthor = new Author({
            name,
            birthplace,
            birthdate: formattedDate,
            biography,
            avatarUrl,
        });
        await newAuthor.save();
        res.status(201).json({
            message: "Thêm tác giả thành công!",
            author: newAuthor,
        });
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi thêm tác giả",
            details: error.message,
        });
    }
};

// Sửa thông tin tác giả
const updateAuthor = async (req, res) => {
    try {
        const { id } = req.params;
        const { name, birthplace, birthdate, biography, avatarUrl } = req.body;
        const dateParts = birthdate.split("/");
        const formattedDate = new Date(
            Date.UTC(dateParts[2], dateParts[1] - 1, dateParts[0])
        );
        const updatedAuthor = await Author.findByIdAndUpdate(
            id,
            {
                name,
                birthplace,
                birthdate: formattedDate,
                biography,
                avatarUrl,
            },
            { new: true }
        );

        if (!updatedAuthor) {
            return res.status(404).json({ error: "Không tìm thấy tác giả" });
        }

        res.status(200).json({
            message: "Cập nhật tác giả thành công!",
            author: updatedAuthor,
        });
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi cập nhật tác giả",
            details: error.message,
        });
    }
};

// Xóa tác giả
const deleteAuthor = async (req, res) => {
    try {
        const { id } = req.params;
        const deletedAuthor = await Author.findByIdAndDelete(id);

        if (!deletedAuthor) {
            return res.status(404).json({ error: "Không tìm thấy tác giả" });
        }

        res.status(200).json({ message: "Xóa tác giả thành công!" });
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi xóa tác giả",
            details: error.message,
        });
    }
};

// Lấy danh sách tác giả
const getAllAuthors = async (req, res) => {
    try {
        const authors = await Author.find();
        res.status(200).json(authors);
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi lấy danh sách tác giả",
            details: error.message,
        });
    }
};

// Lấy chi tiết tác giả theo ID
const getAuthorById = async (req, res) => {
    try {
        const { id } = req.params;
        const author = await Author.findById(id);

        if (!author) {
            return res.status(404).json({ error: "Không tìm thấy tác giả" });
        }

        res.status(200).json(author);
    } catch (error) {
        res.status(500).json({
            error: "Lỗi khi lấy thông tin tác giả",
            details: error.message,
        });
    }
};

// Xuất các hàm
module.exports = {
    addAuthor,
    updateAuthor,
    deleteAuthor,
    getAllAuthors,
    getAuthorById,
};
