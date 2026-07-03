require "sqlite3"

module DB
  PATH = File.expand_path("../db/hotelya.db", __dir__)
  SCHEMA_PATH = File.expand_path("../db/schema.sql", __dir__)

  def self.connection
    conn = SQLite3::Database.new(PATH)
    conn.results_as_hash = true
    conn.execute("PRAGMA foreign_keys = ON")
    conn
  end

  # Creates hotelya.db from schema.sql if it doesn't exist yet.
  def self.setup!
    return if File.exist?(PATH)

    conn = SQLite3::Database.new(PATH)
    conn.execute_batch(File.read(SCHEMA_PATH))
    conn.close
  end
end
