// Database initialization script
db = db.getSiblingDB('audiobooksDB');

// Create collections
db.createCollection('users');
db.createCollection('books');
db.createCollection('chapters');
db.createCollection('comments');
db.createCollection('ratings');
db.createCollection('authors');
db.createCollection('otp');
db.createCollection('texts');
db.createCollection('audios');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "accountname": 1 }, { unique: true });
db.books.createIndex({ "title": 1 });
db.books.createIndex({ "author": 1 });
db.chapters.createIndex({ "book_id": 1 });
db.comments.createIndex({ "book_id": 1 });
db.comments.createIndex({ "user_id": 1 });
db.ratings.createIndex({ "book_id": 1 });
db.ratings.createIndex({ "user_id": 1 });
db.authors.createIndex({ "name": 1 });
db.otp.createIndex({ "email": 1 });
db.otp.createIndex({ "createdAt": 1 }, { expireAfterSeconds: 300 });
db.texts.createIndex({ "user_id": 1 });
db.audios.createIndex({ "text_id": 1 });
db.audios.createIndex({ "user_id": 1 });

// Create admin user for testing
db.users.insertOne({
  accountname: "admin",
  username: "Admin User",
  email: "admin@example.com",
  password: "$2b$10$K7JVVgmzRa5fsAdFqkqIg.PiVXCvhGvxLCYN1OxsUQpE5YbTlB2Wu", // "password"
  favorite: ["Khoa Học", "Bí Ẩn"],
  createdAt: new Date(),
  updatedAt: new Date()
});

// Create some test authors
const authors = [
  {
    name: "Tô Hoài",
    birthplace: "Hà Nội",
    birthdate: new Date("1920-09-27"),
    biography: "Tô Hoài là một nhà văn Việt Nam nổi tiếng với nhiều tác phẩm văn học dành cho thiếu nhi.",
    avatarUrl: "https://upload.wikimedia.org/wikipedia/vi/0/04/T%C3%B4_Ho%C3%A0i.jpg",
    books: []
  },
  {
    name: "Nguyễn Nhật Ánh",
    birthplace: "Quảng Nam",
    birthdate: new Date("1955-05-07"),
    biography: "Nguyễn Nhật Ánh là nhà văn Việt Nam nổi tiếng với nhiều tác phẩm văn học thiếu nhi và tình cảm học đường.",
    avatarUrl: "https://upload.wikimedia.org/wikipedia/commons/b/b7/Nh%C3%A0_v%C4%83n_Nguy%E1%BB%85n_Nh%E1%BA%ADt_%C3%81nh.jpg",
    books: []
  }
];

db.authors.insertMany(authors);

// Create test books
const authorIds = db.authors.find({}, { _id: 1 }).toArray();
const books = [
  {
    title: "Dế Mèn Phiêu Lưu Ký",
    description: "Dế Mèn phiêu lưu ký là một tác phẩm văn học thiếu nhi của nhà văn Tô Hoài kể về cuộc phiêu lưu của chú Dế Mèn.",
    author: authorIds[0]._id,
    genre: ["Thiếu nhi", "Phiêu lưu"],
    image: "https://salt.tikicdn.com/cache/w1200/ts/product/5e/18/24/2a6154ba08df6ce6161c13f4303fa19e.jpg",
    audio_url: "",
    chapters: [],
    comments: [],
    ratings: [],
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    title: "Tôi Thấy Hoa Vàng Trên Cỏ Xanh",
    description: "Tôi thấy hoa vàng trên cỏ xanh là một tiểu thuyết của nhà văn Nguyễn Nhật Ánh, xuất bản năm 2010.",
    author: authorIds[1]._id,
    genre: ["Tiểu thuyết", "Tình cảm"],
    image: "https://salt.tikicdn.com/cache/w1200/ts/product/2e/eb/ad/f9841ec718f1bf8b0cc6901ec830cc9e.jpg",
    audio_url: "",
    chapters: [],
    comments: [],
    ratings: [],
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

const bookResults = db.books.insertMany(books);
const bookIds = bookResults.insertedIds;

// Update authors with book references
db.authors.updateOne(
  { _id: authorIds[0]._id },
  { $push: { books: bookIds[0] } }
);

db.authors.updateOne(
  { _id: authorIds[1]._id },
  { $push: { books: bookIds[1] } }
);

// Create some chapters for the books
const chapters = [
  {
    book_id: bookIds[0],
    title: "Mở đầu",
    content: "Tôi là Dế Mèn...",
    audio_url: "",
    index: 1,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    book_id: bookIds[0],
    title: "Dế Mèn gặp Dế Trũi",
    content: "Một ngày kia...",
    audio_url: "",
    index: 2,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    book_id: bookIds[1],
    title: "Tuổi thơ",
    content: "Những ngày hè ở làng quê...",
    audio_url: "",
    index: 1,
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    book_id: bookIds[1],
    title: "Tình bạn",
    content: "Tôi và Hậu là đôi bạn thân...",
    audio_url: "",
    index: 2,
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

const chapterResults = db.chapters.insertMany(chapters);
const chapterIds = Object.values(chapterResults.insertedIds);


db.books.updateOne(
  { _id: bookIds[0] },
  { $push: { chapters: { $each: [chapterIds[0], chapterIds[1]] } } }
);

db.books.updateOne(
  { _id: bookIds[1] },
  { $push: { chapters: { $each: [chapterIds[2], chapterIds[3]] } } }
);

// Create sample text for TTS service
db.texts.insertOne({
  user_id: db.users.findOne({accountname: "admin"})._id,
  title: "Đoạn văn mẫu",
  content: "Đây là một đoạn văn mẫu tiếng Việt dùng để thử nghiệm chức năng chuyển văn bản thành giọng nói. Hệ thống chuyển đổi văn bản thành giọng nói (TTS) giúp tạo ra những nội dung nghe được từ văn bản viết, hỗ trợ người dùng trải nghiệm nội dung theo cách dễ dàng hơn.",
  language: "vi",
  tags: ["mẫu", "thử nghiệm"],
  status: "pending",
  word_count: 42,
  created_at: new Date(),
  updated_at: new Date()
});

print("Database initialization completed successfully!");