# Database Schema (ER Diagram)

This diagram visualizes the SQL schema for the day trading app.

```mermaid
erDiagram
    ASSETS {
        int id PK
        string symbol
        string name
    }

    PRICES {
        int id PK
        int asset_id FK
        datetime timestamp
        float open
        float high
        float low
        float close
        int volume
    }

    ACCOUNTS {
        int id PK
        string type
        float cash_balance
        datetime created_at
    }

    TRADES {
        int id PK
        int account_id FK
        int asset_id FK
        string side
        int quantity
        float price
        datetime timestamp
    }

    ASSETS ||--o{ PRICES : has
    ASSETS ||--o{ TRADES : traded_in
    ACCOUNTS ||--o{ TRADES : executes
