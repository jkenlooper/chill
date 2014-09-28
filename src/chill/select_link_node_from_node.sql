select nn.target_node_id as node_id from Node as n
inner join Node_Node as nn on (n.id = nn.node_id)
where n.id = :node_id
order by node_id;
