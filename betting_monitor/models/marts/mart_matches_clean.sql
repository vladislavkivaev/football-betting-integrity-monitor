with intermediate as (

    select * from {{ ref('int_matches_with_features') }}

)

select * from intermediate