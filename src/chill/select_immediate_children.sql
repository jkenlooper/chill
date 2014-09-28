
SELECT n.id, (COUNT(parent.id) - (sub_tree.depth + 1)) AS depth, n.name, n.value
FROM Node as n,
Node AS parent,
Node AS sub_parent,
    (
        SELECT n.id, (COUNT(parent.id) - 1) AS depth, parent.name, parent.value
        FROM Node AS n,
        Node AS parent
            WHERE n.left BETWEEN parent.left AND parent.right
            AND n.id = :node_id
            GROUP BY n.id
            ORDER BY n.left
    ) AS sub_tree
    WHERE n.left BETWEEN parent.left AND parent.right
    AND n.left BETWEEN sub_parent.left AND sub_parent.right
    AND sub_parent.id = sub_tree.id
    GROUP BY n.id
    HAVING depth = 1
    ORDER BY n.left;


-- http://mikehillyer.com/articles/managing-hierarchical-data-in-mysql/
/*
SELECT node.name, (COUNT(parent.name) - (sub_tree.depth + 1)) AS depth
FROM nested_category AS node,
nested_category AS parent,
nested_category AS sub_parent,
(
SELECT node.name, (COUNT(parent.name) - 1) AS depth
FROM nested_category AS node,
nested_category AS parent
WHERE node.lft BETWEEN parent.lft AND parent.rgt
AND node.name = 'PORTABLE ELECTRONICS'
GROUP BY node.name
ORDER BY node.lft
)AS sub_tree
WHERE node.lft BETWEEN parent.lft AND parent.rgt
AND node.lft BETWEEN sub_parent.lft AND sub_parent.rgt
AND sub_parent.name = sub_tree.name
GROUP BY node.name
HAVING depth <= 1
ORDER BY node.lft
*/
