select n.id as node_id, n.name, n.value, t.name as template, q.name as query, r.path, r.method, r.weight from
Node as n
left join Route as r on (n.id == r.node_id)
left join Template as t on (n.template == t.id)
left join Query as q on (n.query == q.id)
