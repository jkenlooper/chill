SELECT t0.name node
    ,GROUP_CONCAT(t5.name) children
    ,(SELECT GROUP_CONCAT(t6.name)
    FROM Node t6
    WHERE t6.left<t0.left AND t6.right>t0.right
    ORDER BY t6.left) ancestors
FROM Node t0
    LEFT JOIN
    (SELECT *
    FROM (SELECT t1.left node
        ,MAX(t2.left) nodeparent
    FROM Node t1
        INNER JOIN
        Node t2 ON t1.left>t2.left AND t1.right<t2.right
    GROUP BY t1.left) t3 
    LEFT JOIN
    Node t4 ON t3.node=t4.left) t5 ON t0.left=t5.nodeparent
GROUP BY t0.name;

/*
-- http://sqlfiddle.com/#!2/c7bac/2
SELECT t0.title node
    ,GROUP_CONCAT(t5.title) children
    ,(SELECT GROUP_CONCAT(t6.title)
    FROM Tree t6
    WHERE t6.lft<t0.lft AND t6.rgt>t0.rgt
    ORDER BY t6.lft) ancestors
FROM Tree t0
    LEFT JOIN
    (SELECT *
    FROM (SELECT t1.lft node
        ,MAX(t2.lft) nodeparent
    FROM Tree t1
        INNER JOIN
        Tree t2 ON t1.lft>t2.lft AND t1.rgt<t2.rgt
    GROUP BY t1.lft) t3 
    LEFT JOIN
    Tree t4 ON t3.node=t4.lft) t5 ON t0.lft=t5.nodeparent
GROUP BY t0.title
*/



/*

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
    HAVING depth <= 1
    ORDER BY n.left
    */


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
