CREATE TABLE IF NOT EXISTS wednesday (
    date TEXT PRIMARY KEY NOT NULL,
    dish_title TEXT,
    dish_description TEXT,
    dish_type TEXT CHECK (dish_type IS NULL OR dish_type IN ('vegan', 'vegetarisch', 'fleisch_fisch'))
);

CREATE TABLE IF NOT EXISTS cook (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL REFERENCES wednesday(date),
    display_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    UNIQUE (date, normalized_name)
);

CREATE TABLE IF NOT EXISTS registration (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL REFERENCES wednesday(date),
    display_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    diet TEXT NOT NULL CHECK (diet IN ('alles', 'vegetarisch', 'vegan')),
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE (date, normalized_name)
);

CREATE TABLE IF NOT EXISTS expense (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL REFERENCES wednesday(date),
    cook_id INTEGER NOT NULL REFERENCES cook(id),
    paid_by_name TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS expense_date_idx ON expense(date);

CREATE TABLE IF NOT EXISTS budget_approval (
    date TEXT PRIMARY KEY NOT NULL REFERENCES wednesday(date),
    approved_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    approved_total_cents INTEGER NOT NULL,
    approved_at TEXT NOT NULL
);
