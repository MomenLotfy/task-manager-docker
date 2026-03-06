CREATE TABLE IF NOT EXISTS books (
    id         SERIAL PRIMARY KEY,
    title      VARCHAR(255) NOT NULL,
    author     VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO books (title, author) VALUES
  ('Clean Code', 'Robert C. Martin'),
  ('The Pragmatic Programmer', 'Andrew Hunt'),
  ('Docker Deep Dive', 'Nigel Poulton');
