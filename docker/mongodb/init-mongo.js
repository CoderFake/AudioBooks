db = db.getSiblingDB('tts_db');

db.createCollection('users');
db.createCollection('texts');
db.createCollection('audios');

// Tạo indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.texts.createIndex({ "user_id": 1 });
db.texts.createIndex({ "title": 1 });
db.audios.createIndex({ "text_id": 1 });
db.audios.createIndex({ "user_id": 1 });

// Tạo admin user (có thể thay đổi trong file .env)
db.users.insertOne({
    username: "admin",
    email: "admin@example.com",
    hashed_password: "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", // password = "password"
    full_name: "Admin User",
    disabled: false,
    is_admin: true,
    created_at: new Date(),
    updated_at: new Date()
});

print('MongoDB initialization completed.');