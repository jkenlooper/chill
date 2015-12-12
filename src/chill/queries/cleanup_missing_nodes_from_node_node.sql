/*
 * When a node is deleted it isn't automatically deleted from the
 * Node_Node table. This will delete all rows from Node_Node that
 * don't have a matching id in Node table.
 */

delete from Node_Node where node_id not in (select id from Node);
