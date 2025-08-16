CREATE DATABASE IF NOT EXISTS seat_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE seat_db;

-- users table
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(200) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'intern',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- insert dummy data as an admin
INSERT INTO users (name, email, password_hash, role)
VALUES (
  'Rachitha',
  'lithmaldulara@gmail.com',
  'pbkdf2:sha256:600000$luGn5K7fRb3hNOkB$4a8033fa3e7a55ce1b947521a0a653883ae3f3357abe95ceed5f959181cce7cb',
  'admin'
);

-- seats
CREATE TABLE IF NOT EXISTS seats (
  id INT AUTO_INCREMENT PRIMARY KEY,
  seat_number VARCHAR(50) NOT NULL,
  location VARCHAR(120),
  status VARCHAR(20) DEFAULT 'available'
);

-- reservations
CREATE TABLE IF NOT EXISTS reservations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  seat_id INT NOT NULL,
  date DATE NOT NULL,
  time_slot VARCHAR(50),
  status VARCHAR(20) DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (seat_id) REFERENCES seats(id) ON DELETE CASCADE
);

-- sample seats
INSERT INTO seats (seat_number, location) 
VALUES ('A1', 'North wing'), ('A2','North wing'), ('B1','South wing');



