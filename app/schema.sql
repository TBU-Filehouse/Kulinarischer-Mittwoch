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
