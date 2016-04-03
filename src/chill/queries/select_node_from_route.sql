select n.name, n.value, n.id, r.node_id, r.path from Node as n
join Route as r on r.node_id = n.id
where r.path = :uri and r.method = :method;
