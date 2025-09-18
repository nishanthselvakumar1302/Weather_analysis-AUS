
CREATE TABLE weather_rain_au (
    Date DATE,
    Location VARCHAR(50),
    MinTemp FLOAT,
    MaxTemp FLOAT,
    Rainfall FLOAT,
    Evaporation FLOAT,
    Sunshine FLOAT,
    WindGustDir VARCHAR(5),
    WindGustSpeed FLOAT,
    WindDir9am VARCHAR(5),
    WindDir3pm VARCHAR(5),
    WindSpeed9am FLOAT,
    WindSpeed3pm FLOAT,
    Humidity9am FLOAT,
    Humidity3pm FLOAT,
    Pressure9am FLOAT,
    Pressure3pm FLOAT,
    Cloud9am FLOAT,
    Cloud3pm FLOAT,
    Temp9am FLOAT,
    Temp3pm FLOAT,
    RainToday VARCHAR(3),
    RainTomorrow VARCHAR(3)
);
select * from weather_rain_au;
SELECT DISTINCT location FROM weather_rain_au;
/*Top 5 rainiest cities*/

SELECT location, ROUND(AVG(rainfall)::numeric, 2) AS avg_rain
FROM weather_rain_au
GROUP BY location
ORDER BY avg_rain DESC
LIMIT 5;

/*Rainfall Seasonality (by Month)*/

SELECT EXTRACT(MONTH FROM date) AS month,
ROUND(AVG(rainfall)::numeric, 2) AS avg_rain
FROM weather_rain_au
GROUP BY month
ORDER BY month;

/*RainTomorrow Probability by Humidity (3pm)*/

SELECT CASE WHEN humidity3pm > 80 THEN 'High Humidity' WHEN humidity3pm BETWEEN 50 AND 80 THEN 'Medium Humidity'ELSE 'Low Humidity'END AS humidity_category,
ROUND(COUNT(*) FILTER (WHERE raintomorrow = 'Yes') * 100.0 / COUNT(*), 2) AS rain_probability
FROM weather_rain_au
GROUP BY humidity_category
ORDER BY rain_probability DESC;
/*Extreme Rainfall Events (Rainfall > 100 mm)*/

SELECT location, COUNT(*) AS extreme_rain_days
FROM weather_rain_au
WHERE rainfall > 100
GROUP BY location
ORDER BY extreme_rain_days DESC
LIMIT 5;
/*Rainfall Trend Over Years*/

SELECT EXTRACT(YEAR FROM date) AS year,
ROUND(AVG(rainfall)::numeric, 2) AS avg_rain
FROM weather_rain_au
GROUP BY year
ORDER BY year;

/*Temperature vs RainTomorrow*/

SELECT CASE WHEN maxtemp > 30 THEN 'Hot Day'WHEN maxtemp BETWEEN 20 AND 30 THEN 'Warm Day'ELSE 'Cool Day'END AS temp_category,
ROUND(COUNT(*) FILTER (WHERE raintomorrow = 'Yes') * 100.0 / COUNT(*),2) AS rain_probability
FROM weather_rain_au
GROUP BY temp_category
ORDER BY rain_probability DESC;

/*WindSpeed vs RainTomorrow*/

SELECT CASE WHEN windspeed3pm > 30 THEN 'Strong Wind'WHEN windspeed3pm BETWEEN 15 AND 30 THEN 'Moderate Wind'ELSE 'Calm Wind'END AS wind_category,
ROUND(COUNT(*) FILTER (WHERE raintomorrow = 'Yes') * 100.0 / COUNT(*), 2) AS rain_probability
FROM weather_rain_au
GROUP BY wind_category
ORDER BY rain_probability DESC;

/*Location with Most Consecutive Rainy Days*/

WITH rainy_days AS (SELECT location, date,LAG(date) OVER (PARTITION BY location ORDER BY date) AS prev_dateFROM weather_rain_au WHERE raintoday = 'Yes')
SELECT location, COUNT(*) AS consecutive_rain_streak
FROM rainy_days WHERE prev_date IS NOT NULL AND date - prev_date = 1
GROUP BY location
ORDER BY consecutive_rain_streak DESC
LIMIT 5;



