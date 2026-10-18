select
    cast(to_char(d, 'YYYYMMDD') as integer)  as date_key,
    cast(d as date)                          as full_date,
    extract(year from d)::int                as year,
    extract(quarter from d)::int             as quarter,
    extract(month from d)::int               as month,
    to_char(d, 'FMMonth')                    as month_name,
    extract(day from d)::int                 as day,
    extract(isodow from d)::int              as day_of_week,
    to_char(d, 'FMDay')                      as day_name,
    extract(isodow from d) in (6, 7)         as is_weekend
from generate_series('2023-01-01'::date, '2026-12-31'::date, interval '1 day') as g(d)
