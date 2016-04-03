select t.id, t.name from Node as n
join Template as t on t.id = n.template
where n.id is :node_id;
