/* 
 * For adding a single node to a node with no children ( a leaf node ).
 */

update Node set right = right + 2
where right > (select left
    from Node
    where id = :target_node_id);

update Node set left = left + 2
where left > (select left
    from Node
    where id = :target_node_id);

insert into Node(name, left, right, value)
select :name, left + 1, left + 2, :value
from Node
where id = :target_node_id;

select max(id) from Node;

/* (stripped out semicolon)

SELECT @myLeft := lft FROM nested_category
WHERE name = '2 WAY RADIOS'

UPDATE nested_category SET rgt = rgt + 2 WHERE rgt > @myLeft
UPDATE nested_category SET lft = lft + 2 WHERE lft > @myLeft

INSERT INTO nested_category(name, lft, rgt) VALUES('FRS', @myLeft + 1, @myLeft + 2)

*/
