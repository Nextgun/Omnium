-- schema.sql

CREATE TABLE IF NOT EXISTS assets (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10)  NOT NULL,
    name   VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS prices (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    asset_id  INT            NOT NULL,
    timestamp DATETIME       NOT NULL,
    open      FLOAT          NOT NULL,
    high      FLOAT          NOT NULL,
    low       FLOAT          NOT NULL,
    close     FLOAT          NOT NULL,
    volume    INT            NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE IF NOT EXISTS accounts (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    type         VARCHAR(20)    NOT NULL,
    cash_balance FLOAT          NOT NULL,
    created_at   DATETIME       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT            NOT NULL,
    asset_id   INT            NOT NULL,
    side       VARCHAR(4)     NOT NULL,
    quantity   INT            NOT NULL,
    price      FLOAT          NOT NULL,
    timestamp  DATETIME       NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (asset_id)   REFERENCES assets(id)
);