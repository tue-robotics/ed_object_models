Contents of the wall directory:
* `map.pgm`: original result of gmapping
* `map.xcf`: gimp file. Use this to edit the map (n.b.: check the layer)
* `heightmap.pgm`: pgm export (from gimp) of the map to use
* `heightmap.stl`: meshfile used by Gazebo, ED, etc.

To convert:
* `rosrun ed ed_heightmap_to_mesh /home/amigo/ros/kinetic/system/src/ed_object_models/models/rwc2019/walls/shape/heightmap.pgm /home/amigo/ros/kinetic/system/src/ed_object_models/models/rwc2019/walls/shape/heigtmap.stl 0.025 2.0 -1.000000 -27.000000`
* `rosrun ed ed_heightmap_to_mesh $HOME/ros/kinetic/system/src/ed_object_models/models/rwc2019/walls/shape/heightmap.pgm $HOME/ros/kinetic/system/src/ed_object_models/models/rwc2019/walls/shape/heigtmap.stl 0.025 2.0 -1.000000 -27.000000`

