import sys
import aosd
import threading
import Queue
import time
import thread

import utils

class Aosd_conf(object):
    line_space = 4
    top_space = 0
    geom_x_offset = 10
    geom_y_offset = 10
    shadow_color = 'black'
    shadow_opacity = 255
    shadow_x_offset = 1
    shadow_y_offset = 1
    fore_opacity = 255
    font = "DejaVu Sans Mono"
    font_size = 10

class Aosd_text_scroll_entry(object):
    STATE_NEW = 0
    STATE_SHOW = 1

    def __init__(self, text, color, use_screen_width_percent):
        utils.init_from_args(self)
        self.time_show = None
        self.line_num = None
        self._setup()
        self.state = Aosd_text_scroll_entry.STATE_NEW

    def show(self):
        self.time_show = time.time()
        self.osd.show()
        self.osd.loop_once()

    def move_to_line(self, line_num):
        y = Aosd_conf.top_space + (line_num * (Aosd_conf.font_size + Aosd_conf.line_space))
        self.osd.set_geometry(self.x, y, self.w, self.h)
        self.osd.loop_once()

    def _setup(self):
        osd = aosd.AosdText()
        osd.set_transparency(aosd.TRANSPARENCY_COMPOSITE)
        if osd.get_transparency() != aosd.TRANSPARENCY_COMPOSITE:
            osd.set_transparency(aosd.TRANSPARENCY_NONE)
        osd.geom_x_offset = Aosd_conf.geom_x_offset
        osd.geom_y_offset = Aosd_conf.geom_y_offset
        osd.shadow_color = Aosd_conf.shadow_color
        osd.shadow_opacity = Aosd_conf.shadow_opacity
        osd.shadow_x_offset = Aosd_conf.shadow_x_offset
        osd.shadow_y_offset = Aosd_conf.shadow_y_offset
        osd.fore_color = self.color
        osd.fore_opacity = Aosd_conf.fore_opacity
        osd.set_font("%s %d" % (Aosd_conf.font, Aosd_conf.font_size))
        osd.wrap = aosd.PANGO_WRAP_WORD_CHAR
        osd.alignment = aosd.PANGO_ALIGN_LEFT
        osd.set_layout_width(osd.get_screen_wrap_width())
        osd.set_text(unicode(self.text, 'UTF-8', 'ignore'))
        self.w, self.h = osd.get_text_size()
        (screen_w, screen_h) = osd.get_screen_size()
        self.x = screen_w - ((screen_w * self.use_screen_width_percent) / 100)
        self.osd = osd

class Aosd_text_scroll(object):
    def __init__(self, entry_timeout=5, use_screen_heigh_percent=50, use_screen_width_percent=45):
        utils.init_from_args(self)
        self.osd = aosd.Aosd()
        self.entries = list()
        self.last_line = 0
        self.todo_new = 0
    
    def append(self, text, color):
        entry = Aosd_text_scroll_entry(text, color, self.use_screen_width_percent)
        self.entries.append(entry)
        self.todo_new += 1

    def render(self):
        (screen_w, screen_h) = self.osd.get_screen_size()
        self.entries_max = ((screen_h * self.use_screen_heigh_percent) / 100) / (Aosd_conf.font_size + Aosd_conf.line_space)
        self.time_render = time.time()
        self._render_1_remove_old()
        self._render_2_scroll_remaining()
        self._render_3_append_new()

    def _render_1_remove_old(self):
        self.todo_scroll = 0
        n = -1
        for entry in self.entries:
            n += 1
            if len(self.entries) < self.entries_max:
                if entry.state != Aosd_text_scroll_entry.STATE_SHOW:
                    continue
                if entry.time_show + self.entry_timeout > self.time_render:
                    continue
            if entry == self.entries[-1]:
                self.last_line = n
            self.entries.remove(entry)
            del entry
            self.todo_scroll += 1

    def _render_2_scroll_remaining(self):
        if self.last_line < self.entries_max:
            if self.todo_scroll == 0:
                return
            if len(self.entries) + self.todo_new < self.entries_max:
                # do not scroll when not necessary
                return
        n = -1
        for entry in self.entries:
            n += 1
            if entry.state != Aosd_text_scroll_entry.STATE_SHOW:
                continue
            entry.move_to_line(n)
        self.last_line = n
        self.todo_scroll = 0

    def _render_3_append_new(self):
        if self.todo_new == 0:
            return
        n = -1
        for entry in self.entries:
            n += 1
            if entry.state != Aosd_text_scroll_entry.STATE_NEW:
                continue
            entry.move_to_line(self.last_line)
            self.last_line += 1
            entry.show()
            entry.state = Aosd_text_scroll_entry.STATE_SHOW
        self.todo_new = 0

class Aosd_text_scroll_thread(Aosd_text_scroll, threading.Thread):
    def __init__(self, **kwargs):
        Aosd_text_scroll.__init__(self, **kwargs)
        threading.Thread.__init__(self)
        self.queue = Queue.Queue()

    def run(self): # Thread
        while True:
            try:
                to_append = self.queue.get(True, 0.1) # XXX ugly timeout
            except Queue.Empty:
                pass
            else:
                if to_append[0] == "exit":
                    thread.exit()
                Aosd_text_scroll.append(self, to_append[0], to_append[1])
            Aosd_text_scroll.render(self)

    def append(self, text, color): # Aosd_text_scroll
        to_append = [text, color]
        self.queue.put_nowait(to_append)

    def render(self): # Aosd_text_scroll
        raise Exception("You should not call render on this class, it is already done inside the thread")

    def exit(self):
        self.append("exit", "now")
