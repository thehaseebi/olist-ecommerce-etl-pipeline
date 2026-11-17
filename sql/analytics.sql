-- 1 Monthly revenue, order count and MoM growth

with monthly as (
    SELECT d.year, d.month, 
           sum(f.total_amount) as revenue,
           count(distinct f.order_id) as orders
    FROM fact_sales f
    JOIN dim_date d USING (date_key)
    WHERE f.order_status = 'delivered'
    GROUP BY d.year, d.month
)

select year, month, revenue, orders, 
       round(100.0 * (revenue - lag(revenue) over w) 
            / NULLIF(lag(revenue) over w, 0), 2) as mom_growth_pct
from monthly
WINDOW w as (order by year, month)
order by year, month;

-- 2. Top 10 product categories by revenue
select p.category, sum(f.total_amount) as revenue
from fact_sales f
join dim_product p using (product_id)
where f.order_status = 'delivered'
group by p.category
order by revenue desc
limit 10;

-- 3. Repeat-customer rate
with per_customer as (
    select c.customer_unique_id, count(distinct f.order_id) as order_count
    from fact_sales f
    join dim_customer c using (customer_id)
    group by c.customer_unique_id
)

select round(100.0 * avg((order_count > 1)::int), 2) as repeat_customer_pct
from per_customer;
