with source as (

    select * from {{ source('raw', 'matches_raw') }}

),

renamed as (

    select
        -- match info (cast + rename to snake_case)
        "Date"::date           as match_date,
        "HomeTeam"             as home_team,
        "AwayTeam"             as away_team,
        "FTHG"::int            as home_goals,
        "FTAG"::int            as away_goals,
        "FTR"                  as full_time_result,

        -- opening odds
        "B365H"::numeric       as b365_open_h,
        "B365D"::numeric       as b365_open_d,
        "B365A"::numeric       as b365_open_a,
        "PSH"::numeric         as ps_open_h,
        "PSD"::numeric         as ps_open_d,
        "PSA"::numeric         as ps_open_a,
        "MaxH"::numeric        as max_open_h,
        "MaxD"::numeric        as max_open_d,
        "MaxA"::numeric        as max_open_a,
        "AvgH"::numeric        as avg_open_h,
        "AvgD"::numeric        as avg_open_d,
        "AvgA"::numeric        as avg_open_a,

        -- closing odds
        "B365CH"::numeric      as b365_close_h,
        "B365CD"::numeric      as b365_close_d,
        "B365CA"::numeric      as b365_close_a,
        "PSCH"::numeric        as ps_close_h,
        "PSCD"::numeric        as ps_close_d,
        "PSCA"::numeric        as ps_close_a,
        "MaxCH"::numeric       as max_close_h,
        "MaxCD"::numeric       as max_close_d,
        "MaxCA"::numeric       as max_close_a,
        "AvgCH"::numeric       as avg_close_h,
        "AvgCD"::numeric       as avg_close_d,
        "AvgCA"::numeric       as avg_close_a,

        -- classification (lowercase, no quotes)
        league,
        season,
        tier,

        -- covid flag derived from season
        case when season = '1920' then true else false end as is_covid_season,

        -- derived features (quoted where they contain capitals)
        "b365_drift_H"         as b365_drift_h,
        "b365_drift_D"         as b365_drift_d,
        "b365_drift_A"         as b365_drift_a,
        "pinnacle_drift_H"     as pinnacle_drift_h,
        "pinnacle_drift_D"     as pinnacle_drift_d,
        "pinnacle_drift_A"     as pinnacle_drift_a,
        "opening_spread_H"     as opening_spread_h,
        "opening_spread_D"     as opening_spread_d,
        "opening_spread_A"     as opening_spread_a,
        "closing_spread_H"     as closing_spread_h,
        "closing_spread_D"     as closing_spread_d,
        "closing_spread_A"     as closing_spread_a,
        max_opening_spread,
        max_closing_spread,
        "spread_change_H"      as spread_change_h,
        "spread_change_D"      as spread_change_d,
        "spread_change_A"      as spread_change_a,
        max_spread_change,
        "b365_vs_market_H"     as b365_vs_market_h,
        "b365_vs_market_D"     as b365_vs_market_d,
        "b365_vs_market_A"     as b365_vs_market_a,
        implied_prob_sum_open,
        implied_prob_sum_close,
        season_quintile

    from source

)

select * from renamed