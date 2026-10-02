-- ============================================================
-- NYC Yellow Taxi - Gold Layer
-- Source: yellow_taxi_silver
-- Scope: January 2019
-- ============================================================


-- ============================================================
-- 1. Gold Summary
-- ============================================================

CREATE OR REPLACE TABLE yellow_taxi_gold_summary AS
SELECT
    COUNT(*) AS total_trips,
    ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
    ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
    ROUND(AVG(total_amount), 2) AS avg_total_amount,
    ROUND(AVG(tip_amount), 2) AS avg_tip_amount,
    ROUND(AVG(trip_duration_minutes), 2) AS avg_trip_duration_minutes,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(SUM(tip_amount), 2) AS total_tips
FROM yellow_taxi_silver
WHERE record_quality = 'VALID';


-- ============================================================
-- 2. Hourly Analysis
-- ============================================================

CREATE OR REPLACE TABLE yellow_taxi_gold_hourly AS
SELECT
    pickup_hour,
    COUNT(*) AS total_trips,
    ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
    ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
    ROUND(AVG(trip_duration_minutes), 2) AS avg_trip_duration_minutes,
    ROUND(AVG(total_amount), 2) AS avg_total_amount
FROM yellow_taxi_silver
WHERE record_quality = 'VALID'
GROUP BY pickup_hour
ORDER BY pickup_hour;


-- ============================================================
-- 3. Daily Analysis
-- ============================================================

CREATE OR REPLACE TABLE yellow_taxi_gold_daily AS
SELECT
    pickup_date,
    COUNT(*) AS total_trips,
    ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
    ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
    ROUND(AVG(trip_duration_minutes), 2) AS avg_trip_duration_minutes,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM yellow_taxi_silver
WHERE record_quality = 'VALID'
GROUP BY pickup_date
ORDER BY pickup_date;


-- ============================================================
-- 4. Weekday Analysis
-- ============================================================

CREATE OR REPLACE TABLE yellow_taxi_gold_weekday AS
SELECT
    DAYOFWEEK(pickup_date) AS weekday_number,
    DATE_FORMAT(pickup_date, 'EEEE') AS weekday_name,
    COUNT(*) AS total_trips,
    ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
    ROUND(AVG(total_amount), 2) AS avg_total_amount,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM yellow_taxi_silver
WHERE record_quality = 'VALID'
GROUP BY
    DAYOFWEEK(pickup_date),
    DATE_FORMAT(pickup_date, 'EEEE')
ORDER BY weekday_number;


-- ============================================================
-- 5. Pickup Location Analysis
-- ============================================================

CREATE OR REPLACE TABLE yellow_taxi_gold_pickup_locations AS
SELECT
    PULocationID AS pickup_location_id,
    COUNT(*) AS total_trips,
    ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
    ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM yellow_taxi_silver
WHERE record_quality = 'VALID'
GROUP BY PULocationID;


-- ============================================================
-- 6. Pickup Location Analysis with Zone Names
-- ============================================================

CREATE OR REPLACE TABLE yellow_taxi_gold_pickup_locations_named AS
SELECT
    g.pickup_location_id,
    z.Borough AS borough,
    z.Zone AS pickup_zone,
    z.service_zone,
    g.total_trips,
    g.avg_trip_distance,
    g.avg_fare_amount,
    g.total_revenue
FROM yellow_taxi_gold_pickup_locations g
LEFT JOIN (
    SELECT
        LocationID,
        Borough,
        Zone,
        service_zone
    FROM read_files(
        'dbfs:/databricks-datasets/nyctaxi/taxizone/taxi_zone_lookup.csv',
        format => 'csv',
        header => true,
        inferSchema => true
    )
) z
ON g.pickup_location_id = z.LocationID;


-- ============================================================
-- 7. Borough Analysis
-- ============================================================

CREATE OR REPLACE TABLE yellow_taxi_gold_borough AS
SELECT
    z.Borough AS borough,
    COUNT(*) AS total_trips,
    ROUND(AVG(s.trip_distance), 2) AS avg_trip_distance,
    ROUND(AVG(s.fare_amount), 2) AS avg_fare_amount,
    ROUND(AVG(s.total_amount), 2) AS avg_total_amount,
    ROUND(SUM(s.total_amount), 2) AS total_revenue
FROM yellow_taxi_silver s
INNER JOIN (
    SELECT
        LocationID,
        Borough
    FROM read_files(
        'dbfs:/databricks-datasets/nyctaxi/taxizone/taxi_zone_lookup.csv',
        format => 'csv',
        header => true,
        inferSchema => true
    )
) z
ON s.PULocationID = z.LocationID
WHERE s.record_quality = 'VALID'
GROUP BY z.Borough
ORDER BY total_trips DESC;
