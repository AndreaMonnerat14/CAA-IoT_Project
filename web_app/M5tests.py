from m5stack import *
from m5stack_ui import *
from uiflow import *
import lvgl as lv

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x000000)

lv.init()

# Create a screen object
scr = lv.obj()
scr.set_style_local_bg_color(scr.PART.MAIN, lv.STATE.DEFAULT, lv.color_hex(0x000000))

# Create the button
btn = lv.btn(scr)
btn.set_size(100, 50)
btn.align(scr, lv.ALIGN.IN_BOTTOM_RIGHT, -10, -10)  # Bottom right with padding

# Create two styles
style_hist = lv.style_t()
style_hist.init()
style_hist.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0x00AFFF))
style_hist.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0x00AFFF))

style_back = lv.style_t()
style_back.init()
style_back.set_bg_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))
style_back.set_border_color(lv.STATE.DEFAULT, lv.color_hex(0xFFFFFF))

# Label for the button
label = lv.label(btn)
label.set_text("hist")
label.align(btn, lv.ALIGN.CENTER, 0, 0)

# Initial style and state
btn.add_style(btn.PART.MAIN, style_hist)
state = False

# Toggle function
def action(obj, event):
    global state
    if event == lv.EVENT.CLICKED:
        if not state:
            btn.add_style(btn.PART.MAIN, style_back)
            label.set_text("back")
        else:
            btn.add_style(btn.PART.MAIN, style_hist)
            label.set_text("hist")
        state = not state

btn.set_event_cb(action)

lv.scr_load(scr)
