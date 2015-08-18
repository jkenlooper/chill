select im.width, im.height, sf.path, pic.created, pic.title, pic.description
from Node as n
join Node_Picture as npic on (n.id = npic.node_id)
join Picture as pic on (npic.picture = pic.id)
join Image as im on (pic.image = im.id)
join StaticFile as sf on (im.staticfile = sf.id)
where n.id = :node_id
;
