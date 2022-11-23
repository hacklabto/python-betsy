Betsy LED Display
=================

A Python package for interacting with the Betsy LED display.


test.py is new code I wrote to use PIL to generate some images. In particular:

**send_reset()**  -- Call this once when each panel boots up, as they boot up in bootloader mode and need to be switched to firmware mode
**send_sn_image()** --This reads the inventory, generates a picture of the serial, and sends it to that address. This is the original intention of my hacking.



Some fun utilities that can write arbitary images:
```
img = Image.open("hl.png")
hl = tile_img(img, 18, crop=False) # False = scale.
#send_images(hl)
```

And send gifs ( in a loop! ) -- This is just above, but parsing the frames from a gif and calling the above **send_images** in a loop
```
while 1:
  handle_gif("./nyan.gif",0.025)
```

Finally, there's some TK stuff I used for visualization when writing this stuff at home, but it's not really useful anymore, and will be removed shortly.
