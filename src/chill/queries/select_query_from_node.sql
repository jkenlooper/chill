select s.id, s.name from SelectSQL as s
join SelectSQL_Node as sn on ( sn.selectsql_id = s.id )
join Node as n on ( n.id = sn.node_id )
where n.id is :node_id 
group by s.id;
