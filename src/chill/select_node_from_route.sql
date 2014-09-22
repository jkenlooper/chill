select Node.name, Node.value, Node.id, route.node_id, route.path from Node
join route on route.node_id = Node.id where route.path = :uri
group by Node.name;
