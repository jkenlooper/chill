select q.id, q.name from Query as q
join Query_Node as sn on ( sn.query_id = q.id )
join Node as n on ( n.id = sn.node_id )
where n.id is :node_id
group by q.id;
