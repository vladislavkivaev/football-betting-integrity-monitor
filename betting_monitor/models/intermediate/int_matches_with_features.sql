with staged as (

    select * from {{ ref('stg_matches') }}

),

features as (

    select
        *,

        -- cross-market gap at close: Bet365 vs Pinnacle (sharp reference)
        -- positive = B365 offered a longer price than Pinnacle at close
        (b365_close_h - ps_close_h) as b365_vs_ps_close_h,
        (b365_close_d - ps_close_d) as b365_vs_ps_close_d,
        (b365_close_a - ps_close_a) as b365_vs_ps_close_a,

        -- overround (bookmaker margin) flags: did the market tighten toward close?
        -- true when the closing implied-prob sum is lower than the opening sum
        case
            when implied_prob_sum_close < implied_prob_sum_open then true
            else false
        end as margin_tightened,

        -- absolute change in overround from open to close
        (implied_prob_sum_close - implied_prob_sum_open) as overround_change,

        -- did the home favourite shorten (drift down) from open to close?
        case
            when b365_drift_h < 0 then true
            else false
        end as home_shortened,

        -- simple result-side helper: did the home team win?
        case
            when full_time_result = 'H' then true
            else false
        end as home_win

    from staged

)

select * from features