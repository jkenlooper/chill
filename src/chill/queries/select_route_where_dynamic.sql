select path as rule, weight, node_id from Route where rule like '%<%>%'
order by weight desc;
