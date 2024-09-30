-- Create 'users' table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user'
);

INSERT INTO users (username, password, role) VALUES ('admin', '$2b$12$x5FUcuyNOmm3UTY1i7PeV.V7k8SI4PlEs03PE2.Nrb6id4MatSH8a', 'admin');
INSERT INTO users (username, password) VALUES ('akshayvijayvergiya@usf.edu', '$2b$12$mscNAUO1O9DZ2wLlb0b9PekldmYaYEzsO8GAdNQGf5dmCVCH4Bq/i');
INSERT INTO users (username, password) VALUES ('vkayhan@usf.edu', '$2b$12$IeZ6jwSVu626O5CV.Vb/PuwBHccXQfp3EU2LkM3s7yYs0JTohVqGW');