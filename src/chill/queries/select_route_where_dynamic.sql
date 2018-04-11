select path as rule, weight, node_id from Route where path like '%<%>%'
order by weight desc;
