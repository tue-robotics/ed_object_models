ED Object Models [![Build Status](https://travis-ci.com/tue-robotics/ed_object_models.svg?branch=master)](https://travis-ci.com/tue-robotics/ed_object_models)
================
Models of entities in our world model [ED](https://github.com/tue-robotics/ed/)

Models can be created with the ```create-model.py``` script. Only Tables, cabinets and boxes are supported by the script at the moment.
The object comes with multiple areas:
 - in_front_of
 - on_top_of
 - near
 
 The areas can be used for manipulation or navigation. The on_top_of area is also used for segmentation purposes. To be robust against errors in your robot model, it starts 2 cm above the object. No research is done for the optimal value. 
