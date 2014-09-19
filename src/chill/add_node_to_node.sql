/* 
 * For adding a single node to a node with children already (not a leaf node).
 */

update Node set right = right + 2
where right > (select right
    from Node
    where id = :target_node_id);

update Node set left = left + 2
where left > (select right
    from Node
    where id = :target_node_id);

insert into Node(name, left, right)
select :name, right + 1, right + 2
from Node
where id = :target_node_id;

select max(id) from Node;

/* (stripped out semicolon)

SELECT @myRight := rgt FROM nested_category
WHERE name = 'TELEVISIONS'

UPDATE nested_category SET rgt = rgt + 2 WHERE rgt > @myRight
UPDATE nested_category SET lft = lft + 2 WHERE lft > @myRight

INSERT INTO nested_category(name, lft, rgt) VALUES('GAME CONSOLES', @myRight + 1, @myRight + 2)

*/
