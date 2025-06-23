WORLD_MAP_RULES = '''
Given the following game scenario, generate an appropriate world map for use in an adventure game based
on Dungeons and Dragons 5th Edition.

The map should first be divided into a number of distinct regions.  A region is a large area with some
consistency to it.  These can include large outdoor areas, settlements like towns and villages, or
a dungeon as a whole.

Examples of regions:
A large forest
The town of Eldoria
A network of caves
An expansive desert

Each region has a unique name and a description containing information that is apparent to the player.
The region also has DM_notes which includes DM-specific information about the region that might not
be known to the player.

Each region contains multiple locations within it.  A location is a distinct area where a player can go.
Unlike regions, locations represent relatively small and contained areas,
so while the Dark Forest would be a region, a fork in the road within the forest would be a location.
Locations may be indoors (like rooms within a dungeon or building) or outdoors (like points of interest in a forest).

Examples of locations:
A town square
The inn within a town
A blacksmith shop
A dungeon corridor
A room filled with treasure
A position on a main road
A spot by the bank of a river

Each location has a unique name.
Each location has a type.  Locations vary greatly by type.  Here are some examples:
  town, city, hamlet.  Location represents a settlement that can in turn contain buildings, etc. 
  forest, mountain, plain, desert.  Location represents an wide outdoor area.  These locations may in turn contain individual points of interest.
  road, path, highway.  Location represents a point along a road or other organized means of travel.
  room, hallway.  Location represents a room indoors.
Each locaiton has a description.  This gives information about what the player can expect to see or encounter
in this location.
Each location also has DM_notes.  These provide information for the dungeon master about the details of the location,
including its level of danger, likely contents, and more.  The player does not necessarily know everything the DM
knows about a location.
Each location lists any items of interest that may be located there.  Items are usually found only in small, contained
locations like dungeon rooms, not out in the open.

Paths connect locations to each either.
Each path has a direction which indicates the general direction that path moves, for example, north, south, east, west, inside, etc.
Each path has a destination which must be the name of another location in the game.
Each path also has a description which provides information about what the player is likely to see or experience when
traversing the path.
A path's distance indicates how far the destination is from the current location.
Finally, each path includes DM_notes which gives the DM information about what might happen to the player along the way.

Paths may connect locations that belong to different regions.
'''