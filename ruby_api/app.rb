require "sinatra"
require "json"
require "securerandom"
require "digest"
require_relative "lib/db"

DB.setup!

before do
  content_type :json
end

helpers do
  def json_body
    JSON.parse(request.body.read)
  rescue JSON::ParserError
    halt 400, { error: "Invalid JSON body" }.to_json
  end

  def require_fields!(body, fields)
    missing = fields.select { |f| body[f].nil? || body[f] == "" }
    halt 400, { error: "Missing fields: #{missing.join(', ')}" }.to_json unless missing.empty?
  end

  def exists?(conn, table, pk_col, id)
    !conn.get_first_row("SELECT 1 FROM #{table} WHERE #{pk_col} = ?", [id]).nil?
  end

  def not_found!(resource)
    halt 404, { error: "#{resource} not found" }.to_json
  end

  def uuid
    SecureRandom.uuid
  end

  def bool_to_int(value)
    value ? 1 : 0
  end
end

# ---------------------------------------------------------------------------
# Catalog: location, hotel, room_type, room, amenity, hotel_amenity,
# room_amenity, service, reward — single-table inserts used to seed the
# hotel catalog (no composite app workflow touches more than one of these
# at a time).
# ---------------------------------------------------------------------------

post "/locations" do
  body = json_body
  require_fields!(body, %w[country city state])
  conn = DB.connection
  id = uuid
  conn.execute("INSERT INTO location (id_location, country, city, state) VALUES (?, ?, ?, ?)",
               [id, body["country"], body["city"], body["state"]])
  status 201
  { id_location: id }.to_json
ensure
  conn&.close
end

post "/hotels" do
  body = json_body
  require_fields!(body, %w[location_id name])
  conn = DB.connection
  not_found!("location") unless exists?(conn, "location", "id_location", body["location_id"])

  id = uuid
  conn.execute(
    "INSERT INTO hotel (id_hotel, location_id, name, description, stars, phone, email, cover_image_url, is_active)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [id, body["location_id"], body["name"], body["description"], body["stars"], body["phone"],
     body["email"], body["cover_image_url"], bool_to_int(body.fetch("is_active", true))]
  )
  status 201
  { id_hotel: id }.to_json
ensure
  conn&.close
end

post "/room_types" do
  body = json_body
  require_fields!(body, %w[name capacity])
  conn = DB.connection
  id = uuid
  conn.execute(
    "INSERT INTO room_type (id_room_type, name, description, base_price, capacity) VALUES (?, ?, ?, ?, ?)",
    [id, body["name"], body["description"], body.fetch("base_price", 0), body["capacity"]]
  )
  status 201
  { id_room_type: id }.to_json
ensure
  conn&.close
end

post "/rooms" do
  body = json_body
  require_fields!(body, %w[hotel_id room_type_id room_number])
  conn = DB.connection
  not_found!("hotel") unless exists?(conn, "hotel", "id_hotel", body["hotel_id"])
  not_found!("room_type") unless exists?(conn, "room_type", "id_room_type", body["room_type_id"])

  id = uuid
  conn.execute(
    "INSERT INTO room (id_room, hotel_id, room_type_id, room_number, floor, is_available, image_url)
     VALUES (?, ?, ?, ?, ?, ?, ?)",
    [id, body["hotel_id"], body["room_type_id"], body["room_number"], body["floor"],
     bool_to_int(body.fetch("is_available", true)), body["image_url"]]
  )
  status 201
  { id_room: id }.to_json
ensure
  conn&.close
end

post "/amenities" do
  body = json_body
  require_fields!(body, %w[name])
  conn = DB.connection
  id = uuid
  conn.execute("INSERT INTO amenity (id_amenity, name, icon, category) VALUES (?, ?, ?, ?)",
               [id, body["name"], body["icon"], body["category"]])
  status 201
  { id_amenity: id }.to_json
ensure
  conn&.close
end

post "/hotel_amenities" do
  body = json_body
  require_fields!(body, %w[hotel_id amenity_id])
  conn = DB.connection
  not_found!("hotel") unless exists?(conn, "hotel", "id_hotel", body["hotel_id"])
  not_found!("amenity") unless exists?(conn, "amenity", "id_amenity", body["amenity_id"])

  conn.execute("INSERT INTO hotel_amenity (hotel_id, amenity_id) VALUES (?, ?)",
               [body["hotel_id"], body["amenity_id"]])
  status 201
  { hotel_id: body["hotel_id"], amenity_id: body["amenity_id"] }.to_json
ensure
  conn&.close
end

post "/room_amenities" do
  body = json_body
  require_fields!(body, %w[room_id amenity_id])
  conn = DB.connection
  not_found!("room") unless exists?(conn, "room", "id_room", body["room_id"])
  not_found!("amenity") unless exists?(conn, "amenity", "id_amenity", body["amenity_id"])

  conn.execute("INSERT INTO room_amenity (room_id, amenity_id) VALUES (?, ?)",
               [body["room_id"], body["amenity_id"]])
  status 201
  { room_id: body["room_id"], amenity_id: body["amenity_id"] }.to_json
ensure
  conn&.close
end

post "/services" do
  body = json_body
  require_fields!(body, %w[hotel_id name price])
  conn = DB.connection
  not_found!("hotel") unless exists?(conn, "hotel", "id_hotel", body["hotel_id"])

  id = uuid
  conn.execute("INSERT INTO service (id_service, hotel_id, name, price, description) VALUES (?, ?, ?, ?, ?)",
               [id, body["hotel_id"], body["name"], body["price"], body["description"]])
  status 201
  { id_service: id }.to_json
ensure
  conn&.close
end

post "/rewards" do
  body = json_body
  require_fields!(body, %w[name stars_cost])
  conn = DB.connection
  id = uuid
  conn.execute(
    "INSERT INTO reward (id_reward, name, description, stars_cost, type, is_active) VALUES (?, ?, ?, ?, ?, ?)",
    [id, body["name"], body["description"], body["stars_cost"], body["type"], bool_to_int(body.fetch("is_active", true))]
  )
  status 201
  { id_reward: id }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Users (registration)
# ---------------------------------------------------------------------------

post "/users" do
  body = json_body
  require_fields!(body, %w[email password name])
  conn = DB.connection
  id = uuid
  password_hash = Digest::SHA256.hexdigest(body["password"])
  conn.execute(
    "INSERT INTO user (id_user, email, password_hash, name, lastname, phone, document_type, document_number, avatar_url, nationality)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [id, body["email"], password_hash, body["name"], body["lastname"], body["phone"], body["document_type"],
     body["document_number"], body["avatar_url"], body["nationality"]]
  )
  status 201
  { id_user: id }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Reservations — one call registers the reservation together with all of
# its guests, mirroring how the app's booking screen collects them as a
# single step before submitting.
# ---------------------------------------------------------------------------

post "/reservations" do
  body = json_body
  require_fields!(body, %w[user_id room_id check_in check_out total_price])
  conn = DB.connection
  not_found!("user") unless exists?(conn, "user", "id_user", body["user_id"])
  not_found!("room") unless exists?(conn, "room", "id_room", body["room_id"])

  reservation_id = uuid
  guests = body.fetch("guests", [])

  conn.transaction do
    conn.execute(
      "INSERT INTO reservation
         (id_reservation, user_id, room_id, check_in, check_out, total_price, status, adults, children, special_requests)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
      [reservation_id, body["user_id"], body["room_id"], body["check_in"], body["check_out"],
       body["total_price"], body.fetch("status", "pending"), body.fetch("adults", 1),
       body.fetch("children", 0), body["special_requests"]]
    )

    guests.each do |guest|
      conn.execute(
        "INSERT INTO guest (id_guest, reservation_id, name, lastname, document_type, document_number, nationality)
         VALUES (?, ?, ?, ?, ?, ?, ?)",
        [uuid, reservation_id, guest["name"], guest["lastname"], guest["document_type"],
         guest["document_number"], guest["nationality"]]
      )
    end

    conn.execute(
      "INSERT INTO notification (id_notification, user_id, reservation_id, title, body, type, is_read)
       VALUES (?, ?, ?, ?, ?, ?, 0)",
      [uuid, body["user_id"], reservation_id, "Reserva creada",
       "Tu reserva ha sido registrada y está pendiente de pago.", "reservation"]
    )
  end

  status 201
  { id_reservation: reservation_id, guests_created: guests.size }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Reservation services — ordering an extra service (room service, spa, etc.)
# against an existing reservation.
# ---------------------------------------------------------------------------

post "/reservation_services" do
  body = json_body
  require_fields!(body, %w[reservation_id service_id])
  conn = DB.connection
  not_found!("reservation") unless exists?(conn, "reservation", "id_reservation", body["reservation_id"])

  service = conn.get_first_row("SELECT price FROM service WHERE id_service = ?", [body["service_id"]])
  not_found!("service") unless service

  quantity = body.fetch("quantity", 1).to_i
  subtotal = service["price"].to_f * quantity
  id = uuid

  conn.execute(
    "INSERT INTO reservation_service (id_reservation_service, reservation_id, service_id, quantity, subtotal)
     VALUES (?, ?, ?, ?, ?)",
    [id, body["reservation_id"], body["service_id"], quantity, subtotal]
  )
  status 201
  { id_reservation_service: id, subtotal: subtotal }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Payments — registering a payment also confirms the reservation and awards
# loyalty stars, the same three effects the app's checkout screen expects
# from a single "pay" action.
# ---------------------------------------------------------------------------

STARS_PER_CURRENCY_UNIT = 10.0 # 1 star earned per 10 (soles/dollars) spent

post "/payments" do
  body = json_body
  require_fields!(body, %w[reservation_id amount])
  conn = DB.connection
  reservation = conn.get_first_row("SELECT user_id FROM reservation WHERE id_reservation = ?", [body["reservation_id"]])
  not_found!("reservation") unless reservation

  payment_id = uuid
  stars_earned = (body["amount"].to_f / STARS_PER_CURRENCY_UNIT).floor

  conn.transaction do
    conn.execute(
      "INSERT INTO payment (id_payment, reservation_id, amount, method, status, paid_at, transaction_id)
       VALUES (?, ?, ?, ?, 'completed', datetime('now'), ?)",
      [payment_id, body["reservation_id"], body["amount"], body["method"], body["transaction_id"]]
    )

    conn.execute("UPDATE reservation SET status = 'confirmed' WHERE id_reservation = ?", [body["reservation_id"]])

    if stars_earned > 0
      conn.execute(
        "INSERT INTO loyalty_transaction (id_loyalty_transaction, user_id, reservation_id, type, stars, description)
         VALUES (?, ?, ?, 'earn', ?, ?)",
        [uuid, reservation["user_id"], body["reservation_id"], stars_earned, "Estrellas ganadas por pago de reserva"]
      )
    end

    conn.execute(
      "INSERT INTO notification (id_notification, user_id, reservation_id, title, body, type, is_read)
       VALUES (?, ?, ?, ?, ?, 'payment', 0)",
      [uuid, reservation["user_id"], body["reservation_id"], "Pago confirmado",
       "Tu pago fue registrado y la reserva ha sido confirmada."]
    )
  end

  status 201
  { id_payment: payment_id, stars_earned: stars_earned }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

post "/reviews" do
  body = json_body
  require_fields!(body, %w[reservation_id user_id hotel_id rating])
  conn = DB.connection
  not_found!("reservation") unless exists?(conn, "reservation", "id_reservation", body["reservation_id"])
  not_found!("user") unless exists?(conn, "user", "id_user", body["user_id"])
  not_found!("hotel") unless exists?(conn, "hotel", "id_hotel", body["hotel_id"])

  id = uuid
  conn.execute(
    "INSERT INTO review (id_review, reservation_id, user_id, hotel_id, rating, comment) VALUES (?, ?, ?, ?, ?, ?)",
    [id, body["reservation_id"], body["user_id"], body["hotel_id"], body["rating"], body["comment"]]
  )
  status 201
  { id_review: id }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Reward redemptions — spends the user's loyalty stars: registers the
# redemption and its matching negative loyalty_transaction together so the
# star balance (SUM of loyalty_transaction.stars) stays consistent.
# ---------------------------------------------------------------------------

post "/reward_redemptions" do
  body = json_body
  require_fields!(body, %w[user_id reward_id])
  conn = DB.connection
  not_found!("user") unless exists?(conn, "user", "id_user", body["user_id"])

  reward = conn.get_first_row("SELECT stars_cost FROM reward WHERE id_reward = ?", [body["reward_id"]])
  not_found!("reward") unless reward

  balance = conn.get_first_value(
    "SELECT COALESCE(SUM(stars), 0) FROM loyalty_transaction WHERE user_id = ?", [body["user_id"]]
  )
  if balance < reward["stars_cost"]
    halt 422, { error: "Insufficient stars", balance: balance, required: reward["stars_cost"] }.to_json
  end

  redemption_id = uuid

  conn.transaction do
    conn.execute(
      "INSERT INTO reward_redemption (id_reward_redemption, user_id, reward_id, reservation_id, stars_spent, status)
       VALUES (?, ?, ?, ?, ?, 'pending')",
      [redemption_id, body["user_id"], body["reward_id"], body["reservation_id"], reward["stars_cost"]]
    )

    conn.execute(
      "INSERT INTO loyalty_transaction
         (id_loyalty_transaction, user_id, reservation_id, reward_redemption_id, type, stars, description)
       VALUES (?, ?, ?, ?, 'redeem', ?, ?)",
      [uuid, body["user_id"], body["reservation_id"], redemption_id, -reward["stars_cost"], "Estrellas usadas para redimir recompensa"]
    )

    conn.execute(
      "INSERT INTO notification (id_notification, user_id, reservation_id, title, body, type, is_read)
       VALUES (?, ?, ?, 'Recompensa redimida', 'Tu recompensa fue registrada y está lista para usar.', 'reward', 0)",
      [uuid, body["user_id"], body["reservation_id"]]
    )
  end

  status 201
  { id_reward_redemption: redemption_id, remaining_stars: balance - reward["stars_cost"] }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Notifications — manual/admin creation, for cases the composite endpoints
# above don't already cover.
# ---------------------------------------------------------------------------

post "/notifications" do
  body = json_body
  require_fields!(body, %w[user_id title body])
  conn = DB.connection
  not_found!("user") unless exists?(conn, "user", "id_user", body["user_id"])

  id = uuid
  conn.execute(
    "INSERT INTO notification (id_notification, user_id, reservation_id, title, body, type, is_read)
     VALUES (?, ?, ?, ?, ?, ?, 0)",
    [id, body["user_id"], body["reservation_id"], body["title"], body["body"], body["type"]]
  )
  status 201
  { id_notification: id }.to_json
ensure
  conn&.close
end

# ---------------------------------------------------------------------------
# Read-only listing routes, kept minimal, purely so inserted rows can be
# verified without opening the .db file directly.
# ---------------------------------------------------------------------------

VERIFIABLE_TABLES = {
  "locations" => %w[location id_location],
  "hotels" => %w[hotel id_hotel],
  "room_types" => %w[room_type id_room_type],
  "rooms" => %w[room id_room],
  "amenities" => %w[amenity id_amenity],
  "services" => %w[service id_service],
  "rewards" => %w[reward id_reward],
  "users" => %w[user id_user],
  "reservations" => %w[reservation id_reservation],
  "guests" => %w[guest id_guest],
  "payments" => %w[payment id_payment],
  "reviews" => %w[review id_review],
  "reward_redemptions" => %w[reward_redemption id_reward_redemption],
  "loyalty_transactions" => %w[loyalty_transaction id_loyalty_transaction],
  "notifications" => %w[notification id_notification],
  "reservation_services" => %w[reservation_service id_reservation_service]
}.freeze

VERIFIABLE_TABLES.each do |path, (table, pk)|
  get "/#{path}" do
    conn = DB.connection
    conn.execute("SELECT * FROM #{table}").to_json
  ensure
    conn&.close
  end

  get "/#{path}/:id" do
    conn = DB.connection
    row = conn.get_first_row("SELECT * FROM #{table} WHERE #{pk} = ?", [params[:id]])
    not_found!(table) unless row
    row.to_json
  ensure
    conn&.close
  end
end
