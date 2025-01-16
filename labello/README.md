

# CAMERA INTRINSEC  : REMARQUE 

la commande `rs-enumerate-devices -c` renvoie : 

  Width:        640
  Height:       480
  PPX:          317.536560058594
  PPY:          235.513336181641
  Fx:           616.884826660156
  Fy:           616.487854003906
  Distortion:   Inverse Brown Conrady
  Coeffs:       0       0       0       0       0  
  FOV (deg):    54.83 x 42.54
  
 Extrinsic from "Depth"    To      "Color" :
 Rotation Matrix:
   0.999961        -0.00187475       0.00860543    
   0.00184501       0.999992         0.00346188    
  -0.00861185      -0.00344586       0.999957     
  
  Translation Vector: 0.0151646453887224  0.000141525495564565  -0.000478783331345767  




les lignes de code suivantes 
```
			depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
			color_intrin = color_frame.profile.as_video_stream_profile().intrinsics
			depth_to_color_extrin = depth_frame.profile.get_extrinsics_to(color_frame.profile)

```

renvoient : 

{'depth_intrin': [ 640x480  p[317.405 232.5]  f[612.043 612.043]  Brown Conrady [0 0 0 0 0] ], 'color_intrin': [ 640x480  p[317.537 235.513]  f[616.885 616.488]  Inverse Brown Conrady [0 0 0 0 0] ], 'depth_to_color_extrin': rotation: [0.999961, 0.00184501, -0.00861185, -0.00187475, 0.999992, -0.00344586, 0.00860543, 0.00346188, 0.999957]
translation: [0.0151646, 0.000141525, -0.000478783]}


On remarque que la commande `rs-enumerate-devices -c` renvoie les memes valeurs que  `color_intrin`
