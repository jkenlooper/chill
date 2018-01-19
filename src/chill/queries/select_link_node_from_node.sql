select ln.id as node_id, ln.name, ln.value from Node as n
join Node_Node as nn on (n.id = nn.node_id)
join Node as ln on (nn.target_node_id = ln.id)
where n.id = :node_id;
