select n.name, n.value, n.id as node_id from Node as n
where n.id = :node_id;
