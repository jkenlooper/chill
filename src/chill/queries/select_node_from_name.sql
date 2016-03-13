select n.name, n.value, n.id as node_id from Node as n
where n.name = :node_name;
