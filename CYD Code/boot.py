import lvgl as lv
import gc

gc.enable()
gc.threshold(5000)

gc.collect()
import display_driver

lv.init()
gc.collect()

import app
app.run()