select t.id, t.name from Template as t
join Template_Node as tn on ( tn.template_id = t.id )
join Node as n on ( n.id = tn.node_id )
where n.id is :node_id 
group by t.id;
