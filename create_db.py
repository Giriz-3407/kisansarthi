import sqlite3
import os
from sqlite3 import Error

DATABASE_NAME = "farm_app.db"

def create_connection(db_file):
    """ create a database connection to the SQLite database specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"SQLite version: {sqlite3.sqlite_version}")
        print(f"Successfully connected to database '{db_file}'")
        # Enable foreign key constraint enforcement
        conn.execute("PRAGMA foreign_keys = ON;")
        print("Foreign key enforcement enabled.")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")

    return conn

def execute_sql(conn, sql_statement):
    """ execute a sql statement
    :param conn: Connection object
    :param sql_statement: a SQL statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(sql_statement)
        # print(f"Executed SQL successfully: {sql_statement[:50]}...") # Optional: for verbose logging
    except Error as e:
        print(f"Error executing SQL: {e}\nStatement: {sql_statement}")

def main():
    # --- SQL Statements for Table Creation ---

    sql_create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone_number TEXT UNIQUE NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

    sql_create_farms_table = """
    CREATE TABLE IF NOT EXISTS farms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        farm_name TEXT NOT NULL,
        location_latitude REAL NULL,
        location_longitude REAL NULL,
        address TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """

    sql_create_lands_table = """
    CREATE TABLE IF NOT EXISTS lands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farm_id INTEGER NOT NULL,
        land_name TEXT NOT NULL,
        area REAL NOT NULL,
        area_unit TEXT NOT NULL,
        soil_type_manual TEXT NULL,
        soil_type_detected TEXT NULL,
        current_planting_id INTEGER NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE,
        FOREIGN KEY (current_planting_id) REFERENCES plantings (id) ON DELETE SET NULL
    );
    """
    # Note: Foreign key to plantings might need to be added later if plantings depends on lands
    #       Or handle potential circular dependency if needed. Here assuming plantings can be created later.

    sql_create_hardware_devices_table = """
    CREATE TABLE IF NOT EXISTS hardware_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hardware_unique_id TEXT UNIQUE NOT NULL,
        farm_id INTEGER NOT NULL,
        assigned_land_id INTEGER NULL,
        device_name TEXT NULL,
        model TEXT NULL,
        status TEXT DEFAULT 'inactive' NOT NULL,
        last_seen_at TEXT NULL,
        registration_date TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_land_id) REFERENCES lands (id) ON DELETE SET NULL
        -- Optionally add: UNIQUE(assigned_land_id) -- if only one device per land allowed
    );
    """

    sql_create_soil_readings_table = """
    CREATE TABLE IF NOT EXISTS soil_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        land_id INTEGER NOT NULL,
        farm_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        received_at TEXT DEFAULT CURRENT_TIMESTAMP,
        ph_value REAL NULL,
        nitrogen_value REAL NULL,
        phosphorus_value REAL NULL,
        potassium_value REAL NULL,
        rainfall REAL NULL,
        temperature_value REAL NULL,
        humidity_value REAL NULL,
        FOREIGN KEY (device_id) REFERENCES hardware_devices (id) ON DELETE CASCADE,
        FOREIGN KEY (land_id) REFERENCES lands (id) ON DELETE CASCADE,
        FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
    );
    """

    sql_create_crops_table = """
    CREATE TABLE IF NOT EXISTS crops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT UNIQUE NOT NULL,
        description TEXT NULL,
        image_url TEXT NULL,
        optimal_ph_min REAL NULL,
        optimal_ph_max REAL NULL,
        optimal_nitrogen_range TEXT NULL,
        optimal_phosphorus_range TEXT NULL,
        optimal_potassium_range TEXT NULL,
        optimal_moisture_range TEXT NULL,
        suitable_soil_types TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

    sql_create_plantings_table = """
    CREATE TABLE IF NOT EXISTS plantings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        land_id INTEGER NOT NULL,
        crop_id INTEGER NOT NULL,
        planting_date TEXT NOT NULL,
        expected_harvest_date TEXT NULL,
        actual_harvest_date TEXT NULL,
        status TEXT DEFAULT 'active' NOT NULL,
        notes TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (land_id) REFERENCES lands (id) ON DELETE CASCADE,
        FOREIGN KEY (crop_id) REFERENCES crops (id) ON DELETE RESTRICT
    );
    """
    # Now we can potentially add the foreign key constraint back to lands if needed,
    # but the current `ON DELETE SET NULL` in lands handles this fine.

    sql_create_diseases_table = """
    CREATE TABLE IF NOT EXISTS diseases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_name TEXT UNIQUE NOT NULL,
        description TEXT NULL,
        symptoms TEXT NULL,
        image_url TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

    sql_create_crop_diseases_table = """
    CREATE TABLE IF NOT EXISTS crop_diseases (
        crop_id INTEGER NOT NULL,
        disease_id INTEGER NOT NULL,
        PRIMARY KEY (crop_id, disease_id),
        FOREIGN KEY (crop_id) REFERENCES crops (id) ON DELETE CASCADE,
        FOREIGN KEY (disease_id) REFERENCES diseases (id) ON DELETE CASCADE
    );
    """

    sql_create_remedies_table = """
    CREATE TABLE IF NOT EXISTS remedies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_id INTEGER NOT NULL,
        remedy_type TEXT NOT NULL,
        description TEXT NOT NULL,
        application_instructions TEXT NULL,
        source TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (disease_id) REFERENCES diseases (id) ON DELETE CASCADE
    );
    """

    sql_create_diagnosis_logs_table = """
    CREATE TABLE IF NOT EXISTS diagnosis_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        land_id INTEGER NULL,
        planting_id INTEGER NULL,
        image_storage_url TEXT NOT NULL,
        crop_name_context TEXT NULL,
        scan_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        detected_disease_id INTEGER NULL,
        confidence_score REAL NULL,
        processing_status TEXT DEFAULT 'pending' NOT NULL,
        lang TEXT DEFAULT 'English',
        error_message TEXT NULL,
        result_json TEXT NULL,
        notes TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (land_id) REFERENCES lands (id) ON DELETE SET NULL,
        FOREIGN KEY (planting_id) REFERENCES plantings (id) ON DELETE SET NULL,
        FOREIGN KEY (detected_disease_id) REFERENCES diseases (id) ON DELETE SET NULL
    );
    """

    sql_create_fertilizers_table = """
    CREATE TABLE IF NOT EXISTS fertilizers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fertilizer_name TEXT UNIQUE NOT NULL,
        type TEXT NULL,
        n_content_percent REAL NULL,
        p_content_percent REAL NULL,
        k_content_percent REAL NULL,
        description TEXT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

    sql_create_recommendations_table = """
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        land_id INTEGER NULL,
        planting_id INTEGER NULL,
        recommendation_type TEXT NOT NULL, -- e.g., 'weekly_tip', 'fertilizer', 'pest_alert'
        recommendation_date TEXT DEFAULT CURRENT_TIMESTAMP,
        title TEXT NULL,
        details TEXT NOT NULL,
        reasoning TEXT NULL,
        related_crop_id INTEGER NULL,
        related_fertilizer_id INTEGER NULL,
        is_read INTEGER DEFAULT 0, -- 0 = Unread, 1 = Read
        is_archived INTEGER DEFAULT 0, -- 0 = Active, 1 = Archived
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign Keys with appropriate cascading rules
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (land_id) REFERENCES lands (id) ON DELETE CASCADE,
        FOREIGN KEY (planting_id) REFERENCES plantings (id) ON DELETE CASCADE,
        FOREIGN KEY (related_crop_id) REFERENCES crops (id) ON DELETE SET NULL,
        FOREIGN KEY (related_fertilizer_id) REFERENCES fertilizers (id) ON DELETE SET NULL
    );
    """

    sql_create_courses_table = """
    CREATE TABLE IF NOT EXISTS Courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link TEXT,
    Description TEXT,
    Rated INTEGER,
    Views INTEGER
    )
"""


    # --- SQL Statements for Index Creation ---

    sql_create_farms_user_id_index = "CREATE INDEX IF NOT EXISTS idx_farms_user_id ON farms (user_id);"
    sql_create_lands_farm_id_index = "CREATE INDEX IF NOT EXISTS idx_lands_farm_id ON lands (farm_id);"
    sql_create_lands_planting_id_index = "CREATE INDEX IF NOT EXISTS idx_lands_planting_id ON lands (current_planting_id);"
    sql_create_devices_farm_id_index = "CREATE INDEX IF NOT EXISTS idx_devices_farm_id ON hardware_devices (farm_id);"
    sql_create_devices_land_id_index = "CREATE INDEX IF NOT EXISTS idx_devices_assigned_land_id ON hardware_devices (assigned_land_id);"
    sql_create_devices_hwid_index = "CREATE INDEX IF NOT EXISTS idx_devices_hardware_unique_id ON hardware_devices (hardware_unique_id);"
    sql_create_readings_device_id_index = "CREATE INDEX IF NOT EXISTS idx_readings_device_id ON soil_readings (device_id);"
    sql_create_readings_land_id_index = "CREATE INDEX IF NOT EXISTS idx_readings_land_id ON soil_readings (land_id);"
    sql_create_readings_farm_id_index = "CREATE INDEX IF NOT EXISTS idx_readings_farm_id ON soil_readings (farm_id);"
    sql_create_readings_timestamp_index = "CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON soil_readings (timestamp);"
    sql_create_plantings_land_id_index = "CREATE INDEX IF NOT EXISTS idx_plantings_land_id ON plantings (land_id);"
    sql_create_plantings_crop_id_index = "CREATE INDEX IF NOT EXISTS idx_plantings_crop_id ON plantings (crop_id);"
    sql_create_plantings_status_index = "CREATE INDEX IF NOT EXISTS idx_plantings_status ON plantings (status);"
    sql_create_remedies_disease_id_index = "CREATE INDEX IF NOT EXISTS idx_remedies_disease_id ON remedies (disease_id);"
    sql_create_diag_logs_user_id_index = "CREATE INDEX IF NOT EXISTS idx_diag_logs_user_id ON diagnosis_logs (user_id);"
    sql_create_diag_logs_land_id_index = "CREATE INDEX IF NOT EXISTS idx_diag_logs_land_id ON diagnosis_logs (land_id);"
    sql_create_diag_logs_planting_id_index = "CREATE INDEX IF NOT EXISTS idx_diag_logs_planting_id ON diagnosis_logs (planting_id);"
    sql_create_diag_logs_disease_id_index = "CREATE INDEX IF NOT EXISTS idx_diag_logs_detected_disease_id ON diagnosis_logs (detected_disease_id);"
    sql_create_diag_logs_timestamp_index = "CREATE INDEX IF NOT EXISTS idx_diag_logs_scan_timestamp ON diagnosis_logs (scan_timestamp);"
    sql_create_reco_user_id_index = "CREATE INDEX IF NOT EXISTS idx_reco_user_id ON recommendations (user_id);"
    sql_create_reco_land_id_index = "CREATE INDEX IF NOT EXISTS idx_reco_land_id ON recommendations (land_id);"
    sql_create_reco_type_index = "CREATE INDEX IF NOT EXISTS idx_reco_recommendation_type ON recommendations (recommendation_type);"
    sql_create_reco_date_index = "CREATE INDEX IF NOT EXISTS idx_reco_recommendation_date ON recommendations (recommendation_date);"
    sql_create_reco_read_index = "CREATE INDEX IF NOT EXISTS idx_reco_is_read ON recommendations (is_read);"


    # --- Create database connection ---
    conn = create_connection(DATABASE_NAME)

    # --- Create tables and indexes ---
    if conn is not None:
        print("\nCreating tables...")
        execute_sql(conn, sql_create_users_table)
        execute_sql(conn, sql_create_farms_table)
        # `plantings` references `lands` and `crops`, so create them first
        execute_sql(conn, sql_create_crops_table)
        # `lands` references `farms` and `plantings` (with SET NULL)
        execute_sql(conn, sql_create_lands_table)
        execute_sql(conn, sql_create_plantings_table)
        # `hardware_devices` references `farms` and `lands`
        execute_sql(conn, sql_create_hardware_devices_table)
        # `soil_readings` references `devices`, `lands`, `farms`
        execute_sql(conn, sql_create_soil_readings_table)
        # `diseases` and `remedies`
        execute_sql(conn, sql_create_diseases_table)
        execute_sql(conn, sql_create_crop_diseases_table)
        execute_sql(conn, sql_create_remedies_table)
        # `diagnosis_logs` references `users`, `lands`, `plantings`, `diseases`
        execute_sql(conn, sql_create_diagnosis_logs_table)
        # `fertilizers`
        execute_sql(conn, sql_create_fertilizers_table)
        # `recommendations` references `users`, `lands`, `plantings`, `crops`, `fertilizers`
        execute_sql(conn, sql_create_recommendations_table)
        execute_sql(conn, sql_create_courses_table)
        print("Tables created (if they didn't exist).")

        print("\nCreating indexes...")
        execute_sql(conn, sql_create_farms_user_id_index)
        execute_sql(conn, sql_create_lands_farm_id_index)
        execute_sql(conn, sql_create_lands_planting_id_index)
        execute_sql(conn, sql_create_devices_farm_id_index)
        execute_sql(conn, sql_create_devices_land_id_index)
        execute_sql(conn, sql_create_devices_hwid_index)
        execute_sql(conn, sql_create_readings_device_id_index)
        execute_sql(conn, sql_create_readings_land_id_index)
        execute_sql(conn, sql_create_readings_farm_id_index)
        execute_sql(conn, sql_create_readings_timestamp_index)
        execute_sql(conn, sql_create_plantings_land_id_index)
        execute_sql(conn, sql_create_plantings_crop_id_index)
        execute_sql(conn, sql_create_plantings_status_index)
        execute_sql(conn, sql_create_remedies_disease_id_index)
        execute_sql(conn, sql_create_diag_logs_user_id_index)
        execute_sql(conn, sql_create_diag_logs_land_id_index)
        execute_sql(conn, sql_create_diag_logs_planting_id_index)
        execute_sql(conn, sql_create_diag_logs_disease_id_index)
        execute_sql(conn, sql_create_diag_logs_timestamp_index)
        execute_sql(conn, sql_create_reco_user_id_index)
        execute_sql(conn, sql_create_reco_land_id_index)
        execute_sql(conn, sql_create_reco_type_index)
        execute_sql(conn, sql_create_reco_date_index)
        execute_sql(conn, sql_create_reco_read_index)
        print("Indexes created (if they didn't exist).")

        # --- Commit changes and close connection ---
        conn.commit()
        conn.close()
        print(f"\nDatabase '{DATABASE_NAME}' setup complete. Connection closed.")
    else:
        print(f"Error! cannot create the database connection to '{DATABASE_NAME}'.")

if __name__ == '__main__':
    main()
