select q.id, q.name from Node as n
join Query as q on q.id = n.query
where n.id is :node_id;
